from celery import shared_task
from django.conf import settings
from .products import ProductService
from business.shopify import ShopifyService
import redis
import logging

logger = logging.getLogger(__name__)

def get_redis_client():
    return redis.Redis.from_url(settings.REDIS_URL)

@shared_task
def recalculate_inventory_task():
    """
    Calculate available stock for products flagged
    """
    client = get_redis_client()
    key = settings.REDIS_INVENTORY_DIRTY_SET_KEY
    processed_count = 0
    
    try:
        product_ids = client.spop(key, count=10)
        
        if not product_ids:
            return "No products to process."

        logger.info(f"Recalculating inventory for {len(product_ids)} products...")
        
        for pid_bytes in product_ids:
            try:
                pid = int(pid_bytes)
                ProductService.recalculate_inventory(pid)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing product ID {pid_bytes}: {e}")
                
        return f"Processed {processed_count} products."

    except Exception as e:
        logger.error(f"Error in recalculate_inventory_task: {e}")
        return f"Error: {e}"

@shared_task
def sync_shopify_orders_task():
    """
    Sync orders from all active Shopify stores.
    """
    logger.info("Starting Shopify Order Sync...")
    results = ShopifyService.sync_all_active_shops()
    logger.info(f"Shopify Order Sync Finished: {results}")
    return results