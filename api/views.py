from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
            customer_email=data['customer_email']
        )
        serializer.instance = instance

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        self._check_object()
        try:
            order = OrderService.confirm_payment(pk)
            return Response(self.get_serializer(order).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        self._check_object()
        try:
            order = OrderService.ship_order(pk)
            return Response(self.get_serializer(order).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        self._check_object()
        try:
            order = OrderService.cancel_order(pk)
            return Response(self.get_serializer(order).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def _check_object(self):
        self.get_object()