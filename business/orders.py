from django.db import transaction
from domain.models import Order, OrderLine, Address

class OrderService:
    @classmethod
    @transaction.atomic
    def create_update_order(cls, reference, shipping_address_data, order_lines_data, customer_email, status=Order.Status.WAITING_PAYMENT):
        """
        Creates or updates an Order based on the reference.
        """
        order = Order.objects.filter(reference=reference).first()
        if order:
            return cls._update_order(order, shipping_address_data, order_lines_data, customer_email, status)
        return cls._create_order(reference, shipping_address_data, order_lines_data, customer_email, status)

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
        return order

    @classmethod
    def _update_order(cls, order, shipping_address_data, order_lines_data, customer_email, status):

        address = order.shipping_address
        for key, value in shipping_address_data.items():
            setattr(address, key, value)
        address.save()

        order.customer_email = customer_email
        order.status = status
        order.save()

        order.order_lines.all().delete()
        cls._create_lines(order, order_lines_data)
        return order

    @classmethod
    def _create_lines(order, order_lines_data):
        for line_data in order_lines_data:
            OrderLine.objects.create(order=order, **line_data)
