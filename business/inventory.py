import logging
from django.db import transaction
from django.db.models import Sum
from domain.models import Product, Order, OrderLine
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


def get_redis_client():
    return redis.Redis.from_url(settings.REDIS_URL)


def mark_product_as_dirty(product_id):
    """
    Marks a product for inventory recalculation
    """
    try:
        client = get_redis_client()
        client.sadd(settings.REDIS_INVENTORY_DIRTY_SET_KEY, product_id)
    except Exception as e:
        logger.error(
            f"Error for product {product_id} : {e}")


@transaction.atomic
def recalculate_inventory(product_id):
    """
    Calculates the available stock for a product and updates the database.
    """
    try:
        product = Product.objects.select_for_update().get(pk=product_id)

        reserved_agg = OrderLine.objects.filter(
            product=product
        ).exclude(
            order__status__in=[Order.Status.CANCELED, Order.Status.SHIPPED]
        ).aggregate(total_reserved=Sum('quantity'))

        reserved_quantity = reserved_agg['total_reserved'] or 0

        new_available = product.physical_stock - reserved_quantity

        if product.available_stock != new_available:
            product.available_stock = new_available
            product.save(update_fields=['available_stock'])

    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(
            f"Error for product {product_id}: {e}")