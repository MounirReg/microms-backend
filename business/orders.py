from django.db import transaction
from domain.models import Order, OrderLine, Address

class OrderService:
    @classmethod
    @transaction.atomic
    def create_update_order(cls, reference, shipping_address_data, order_lines_data, customer_email, status=None):
        """
        Creates or updates an Order based on the reference.
        """
        order = Order.objects.filter(reference=reference).first()
        if order:
            return cls._update_order(order, shipping_address_data, order_lines_data, customer_email, status)
        
        final_status = status or Order.Status.WAITING_PAYMENT
        return cls._create_order(reference, shipping_address_data, order_lines_data, customer_email, final_status)

    @classmethod
    @transaction.atomic
    def confirm_payment(cls, order_id):
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.WAITING_PAYMENT:
            raise ValueError(f"Cannot confirm payment for order in status {order.status}")
        order.status = Order.Status.TO_BE_PREPARED
        order.save()
        return order

    @classmethod
    @transaction.atomic
    def ship_order(cls, order_id):
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.TO_BE_PREPARED:
            raise ValueError(f"Cannot ship order in status {order.status}")
        order.status = Order.Status.SHIPPED
        order.save()
        return order

    @classmethod
    @transaction.atomic
    def cancel_order(cls, order_id):
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status == Order.Status.SHIPPED:
            raise ValueError("Cannot cancel an order that has already been shipped")
        order.status = Order.Status.CANCELED
        order.save()
        return order

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
        if status:
            order.status = status
        order.save()

        order.order_lines.all().delete()
        cls._create_lines(order, order_lines_data)
        return order

    @classmethod
    def _create_lines(order, order_lines_data):
        for line_data in order_lines_data:
            OrderLine.objects.create(order=order, **line_data)
