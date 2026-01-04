from domain.models import Order, OrderLine, Product
from django.conf import settings
import redis
import logging

class ProductService:
    logger = logging.getLogger(__name__)

    @staticmethod
    def _get_redis_client():
        return redis.Redis.from_url(settings.REDIS_URL)

    @classmethod
    def mark_products_dirty(cls, order):
        lines = order.order_lines.all()
        for line in lines:
            cls._mark_product_as_dirty(line.product.id)

    @classmethod
    def _mark_product_as_dirty(cls, product_id):
        """
        Marks a product for inventory recalculation
        """
        try:
            client = cls._get_redis_client()
            client.sadd(settings.REDIS_INVENTORY_DIRTY_SET_KEY, product_id)
        except Exception as e:
            cls.logger.error(
                f"Error for product {product_id} : {e}")
