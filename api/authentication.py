from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings

class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            return None

        if api_key == settings.MICRO_OMS_API_KEY:
            class SimpleUser:
                is_authenticated = True
                def __str__(self):
                    return "API User"
            
            return (SimpleUser(), None)

        raise exceptions.AuthenticationFailed('Invalid API Key')
