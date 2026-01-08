from domain.models import Order, OrderLine, Address
from business.products import ProductService
from django.db import transaction

class OrderRepository:

    @classmethod
    def create_update_order(cls, reference, shipping_address_data, order_lines_data, customer_email, status=None):
        order = Order.objects.filter(reference=reference).first()
        if order:
            return cls._update_order(order, shipping_address_data, order_lines_data, customer_email, status)
        
        final_status = status or Order.Status.WAITING_PAYMENT
        return cls._create_order(reference, shipping_address_data, order_lines_data, customer_email, final_status)
    
    @classmethod
    def _create_order(cls, reference, shipping_address_data, order_lines_data, customer_email, status):
        address = Address.objects.create(**shipping_address_data)
        order = Order.objects.create(
            reference=reference,
            shipping_address=address,
            customer_email=customer_email,
            status=status
        )
        cls._create_lines(order, order_lines_data)
        ProductService.mark_products_dirty(order)
        return order

    @classmethod
    def _update_order(cls, order, shipping_address_data, order_lines_data, customer_email, status):

        address = order.shipping_address
        for key, value in shipping_address_data.items():
            setattr(address, key, value)
        address.save()

        order.customer_email = customer_email
        if status:
            order.status = status
        order.save()

        order.order_lines.all().delete()
        cls._create_lines(order, order_lines_data)
        ProductService.mark_products_dirty(order)
        return order
    
    @classmethod
    def _create_lines(cls, order, order_lines_data):
        for line_data in order_lines_data:
            OrderLine.objects.create(order=order, **line_data)