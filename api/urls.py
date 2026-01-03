from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, OrderViewSet
from .shopify_oauth import ShopifyInstallView, ShopifyCallbackView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('shopify/install/', ShopifyInstallView.as_view(), name='shopify-install'),
    path('shopify/callback/', ShopifyCallbackView.as_view(), name='shopify-callback'),
]
