import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import urllib.parse
import hashlib
import hmac
import base64
from domain.models import ShopifyConfig

class ShopifyInstallView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        shop = request.GET.get('shop')
        if not shop:
            return Response({'error': 'Missing shop parameter.'}, status=400)

        scopes = settings.SHOPIFY_SCOPES
        redirect_uri = settings.SHOPIFY_REDIRECT_URI
        api_key = settings.SHOPIFY_API_KEY
        
        state = 'TEST-SECRET' 

        params = {
            'client_id': api_key,
            'scope': scopes,
            'redirect_uri': redirect_uri,
            'state': state
        }
        encoded_params = urllib.parse.urlencode(params)
        
        auth_url = f"https://{shop}/admin/oauth/authorize?{encoded_params}"

        return HttpResponseRedirect(auth_url)

class ShopifyCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.GET.dict()
        
        hmac_param = params.get('hmac')
        if not hmac_param:
            return Response({'error': 'No HMAC provided'}, status=400)
            
        params.pop('hmac', None)
        
        sorted_params = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        secret = settings.SHOPIFY_API_SECRET.encode('utf-8')
        message = sorted_params.encode('utf-8')
        digest = hmac.new(secret, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(digest, hmac_param):
            return Response({'error': 'Invalid HMAC'}, status=403)

        shop = params.get('shop')
        code = params.get('code')
        
        access_token_url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            'client_id': settings.SHOPIFY_API_KEY,
            'client_secret': settings.SHOPIFY_API_SECRET,
            'code': code
        }
        
        response = requests.post(access_token_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            
            config, created = ShopifyConfig.objects.update_or_create(
                shop_url=shop,
                defaults={'access_token': access_token}
            )
            
            return Response({
                'message': 'Auth successful and configuration saved!',
                'shop': shop,
                'config_id': config.id,
                'created': created
            })
        else:
            return Response({'error': 'Failed to get access token', 'details': response.text}, status=400)
