from rest_framework import viewsets
from domain.models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from business.orders import OrderService
from .filters import OrderFilter

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    filterset_class = OrderFilter

    def perform_create(self, serializer):
        data = serializer.validated_data
        
        instance = OrderService.create_update_order(
            reference=data['reference'],
            shipping_address_data=data['shipping_address'],
            order_lines_data=data['order_lines'],
            customer_email=data['customer_email'],
            status=data.get('status', Order.Status.WAITING_PAYMENT)
        )
        serializer.instance = instance