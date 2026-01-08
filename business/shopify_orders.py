import logging
import requests
from datetime import timedelta
from django.utils import timezone
from domain.models import Order, Product, ShopifyConfig
from business.orders import OrderService

logger = logging.getLogger(__name__)

class ShopifyOrderService:
    @classmethod
    def sync_all_active_shops(cls):
        configs = ShopifyConfig.objects.filter(active=True)
        results = {}
        for config in configs:
            results[config.shop_url] = cls.sync_store_orders(config)
        return results

    @classmethod
    def sync_store_orders(cls, config):
        shop_url = config.shop_url
        access_token = config.access_token
        
        url = f"https://{shop_url}/admin/api/2024-01/orders.json"
        headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
        params = {"status": "any", "limit": 250, "updated_at_min": cls._get_last_sync_time(config)}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            orders_data = response.json().get("orders", [])
            
            stats = cls._process_orders_batch(orders_data)
            
            config.last_sync_at = timezone.now()
            config.save()
            return stats
        except Exception as e:
            logger.error(f"Error syncing {shop_url}: {e}")
            return {"created": 0, "updated": 0, "error": str(e)}

    @classmethod
    def _get_last_sync_time(cls, config):
        if config.last_sync_at:
            return (config.last_sync_at - timedelta(minutes=1)).isoformat()
        return (timezone.now() - timedelta(days=30)).isoformat()

    @classmethod
    def _process_orders_batch(cls, orders_data):
        created_count = 0
        updated_count = 0
        for data in orders_data:
            try:
                created = cls._process_single_order(data)
                if created: created_count += 1
                else: updated_count += 1
            except Exception as e:
                logger.error(f"Error processing order {data.get('order_number')}: {e}")
        return {"created": created_count, "updated": updated_count}

    @classmethod
    def _process_single_order(cls, data):
        reference = str(data.get('order_number'))
        is_new = not Order.objects.filter(reference=reference).exists()

        order_lines_data, all_products_exist = cls._extract_lines(data)
        status = cls._map_status(data, has_error=not all_products_exist)
        
        if status == Order.Status.ERROR:
            order_lines_data = []

        shipping_address_data = cls._extract_address(data)

        OrderService.create_update_order(
            reference=reference,
            customer_email=data.get("email") or "no-email@example.com",
            shipping_address_data=shipping_address_data,
            order_lines_data=order_lines_data,
            status=status
        )
        return is_new

    @classmethod
    def _extract_lines(cls, data):
        lines_data_raw = data.get("line_items", [])
        order_lines_data = []
        all_products_exist = True
        
        for line in lines_data_raw:
            sku = line.get("sku")
            product = Product.objects.filter(sku=sku).first()
            if product:
                order_lines_data.append({
                    "product": product,
                    "quantity": line.get("quantity"),
                    "unit_price": float(line.get("price"))
                })
            else:
                all_products_exist = False
                break
        return order_lines_data, all_products_exist

    @classmethod
    def _extract_address(cls, data):
        ship_addr = data.get("shipping_address") or {}
        return {
            "name": ship_addr.get("name", "Inconnu"),
            "street": ship_addr.get("address1", ""),
            "postal_code": ship_addr.get("zip", ""),
            "country_code": ship_addr.get("country_code", "FR")
        }

    @classmethod
    def _map_status(cls, data, has_error=False):
        if has_error: return Order.Status.ERROR
        if data.get("cancelled_at"): return Order.Status.CANCELED
        if data.get("fulfillment_status") == 'fulfilled': return Order.Status.SHIPPED
        if data.get("financial_status") in ['paid', 'partially_paid']:
            return Order.Status.TO_BE_PREPARED
        return Order.Status.WAITING_PAYMENT
