from domain.models import Order, OrderLine, Product
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
import redis
import logging

class ProductService:
    logger = logging.getLogger(__name__)

    @staticmethod
    def _get_redis_client():
        return redis.Redis.from_url(settings.REDIS_URL)

    @classmethod
    @transaction.atomic
    def recalculate_inventory(cls, product_id):
        """
        Calculates the available stock for a product and updates the database.
        """
        try:
            product = Product.objects.select_for_update().get(pk=product_id)

            reserved_agg = OrderLine.objects.filter(
                product=product
            ).exclude(
                order__status__in=[Order.Status.CANCELED, Order.Status.SHIPPED, Order.Status.ERROR]
            ).aggregate(total_reserved=Sum('quantity'))

            reserved_quantity = reserved_agg['total_reserved'] or 0

            new_available = product.physical_stock - reserved_quantity

            if product.available_stock != new_available:
                product.available_stock = new_available
                # Update only available_stock to avoid recursion or side effects if save() was overridden
                product.save(update_fields=['available_stock']) 

        except Product.DoesNotExist:
            cls.logger.warning(f"Product {product_id} not found")
        except Exception as e:
            cls.logger.error(
                f"Error for product {product_id}: {e}")

    @classmethod
    def save_product(cls, product):
        product.save()
        cls.mark_product_as_dirty(product.id)
        return product

    @classmethod
    def mark_products_dirty(cls, order):
        lines = order.order_lines.all()
        for line in lines:
            cls.mark_product_as_dirty(line.product.id)

    @classmethod
    def mark_product_as_dirty(cls, product_id):
        """
        Marks a product for inventory recalculation
        """
        try:
            client = cls._get_redis_client()
            client.sadd(settings.REDIS_INVENTORY_DIRTY_SET_KEY, product_id)
        except Exception as e:
            cls.logger.error(
                f"Error for product {product_id} : {e}")
            
    @classmethod
    def decrement_physical_stock(cls, product, quantity):
        product.physical_stock -= quantity
        cls.save_product(product)
