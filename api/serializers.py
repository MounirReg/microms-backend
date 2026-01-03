from rest_framework import serializers
from django.db import transaction
from domain.models import Product, Address, Order, OrderLine

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'physical_stock', 'available_stock', 'pictureUrl']

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'pictureUrl']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'name', 'street', 'postal_code', 'country_code']

class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ['id', 'product', 'quantity', 'unit_price']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['product'] = ProductMiniSerializer(instance.product).data
        return response

class OrderSerializer(serializers.ModelSerializer):
    shipping_address = AddressSerializer()
    order_lines = OrderLineSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'reference', 'shipping_address', 'order_lines', 'total_price', 'customer_email', 'created_at', 'updated_at', 'status']

    def get_total_price(self, obj):
        total = sum(line.unit_price * line.quantity for line in obj.order_lines.all())
        return total
