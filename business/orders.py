from django.db import transaction
from domain.models import Order
from business.products import ProductService
from business.shopify_orders import ShopifyOrderService

class OrderService:


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
    def ship_order(cls, order_id, tracking_info=None):
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.TO_BE_PREPARED:
            raise ValueError(f"Cannot ship order in status {order.status}")
        order.status = Order.Status.SHIPPED
        order.save()

        cls._decrement_physical_stock(order.order_lines.all())

        tracking = tracking_info or {}
        ShopifyOrderService.fulfill_order(order, tracking)

        return order
    
    @classmethod
    def _decrement_physical_stock(cls, order_lines):
        for line in order_lines:
            quantity = line.quantity
            product = line.product
            ProductService.decrement_physical_stock(product, quantity)


    @classmethod
    @transaction.atomic
    def cancel_order(cls, order_id):
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status == Order.Status.SHIPPED:
            raise ValueError("Cannot cancel an order that has already been shipped")
        order.status = Order.Status.CANCELED
        order.save()
        ProductService.mark_products_dirty(order)
        return order





    @classmethod
    def get_available_actions(cls, status):
        actions = []
        if status == Order.Status.WAITING_PAYMENT:
            actions.append('pay')
            actions.append('cancel')
        elif status == Order.Status.TO_BE_PREPARED:
            actions.append('ship')
            actions.append('cancel')
        elif status == Order.Status.ERROR:
            actions.append('cancel')
        return actions
