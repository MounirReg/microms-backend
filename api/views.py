from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from domain.models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from business.orders import OrderService
from business.products import ProductService
from .filters import OrderFilter

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        instance = Product(**serializer.validated_data)
        ProductService.save_product(instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)
        ProductService.save_product(instance)


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
            tracking_info = request.data if request.data else None
            order = OrderService.ship_order(pk, tracking_info)
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

    @action(detail=True, methods=['get'])
    def available_actions(self, request, pk=None):
        order = self.get_object()
        actions = OrderService.get_available_actions(order.status)
        return Response(actions)
        
    def _check_object(self):
        self.get_object()