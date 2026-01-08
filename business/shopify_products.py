import logging
import requests
from domain.models import ShopifyProduct

logger = logging.getLogger(__name__)

class ShopifyProductService:
    @classmethod
    def ensure_shopify_product_link(cls, config, product):
        link = ShopifyProduct.objects.filter(config=config, product=product).first()
        if link:
            return link

        inventory_item_id = cls._fetch_inventory_item_id(config, product.sku)
        if inventory_item_id:
            link = ShopifyProduct.objects.create(
                config=config,
                product=product,
                inventory_item_id=inventory_item_id
            )
            return link
        else:
            logger.warning(f"Could not find Shopify variant for SKU {product.sku}")
            return None

    @classmethod
    def push_inventory_to_shopify(cls, product):
        from domain.models import ShopifyConfig
        
        configs = ShopifyConfig.objects.filter(active=True)
        for config in configs:
            link = cls.ensure_shopify_product_link(config, product)
            if link:
                cls.update_stock(config, link, product.available_stock)

    @classmethod
    def _fetch_inventory_item_id(cls, config, sku):
        query = """
        query($sku_filter: String!) {
          productVariants(first: 1, query: $sku_filter) {
            edges {
              node {
                inventoryItem {
                  id
                }
              }
            }
          }
        }
        """
        
        variables = {"sku_filter": f"sku:{sku}"}
        
        url = f"https://{config.shop_url}/admin/api/2024-10/graphql.json"
        headers = {
            "X-Shopify-Access-Token": config.access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            edges = data.get("data", {}).get("productVariants", {}).get("edges", [])
            if not edges:
                return None
                
            gid = edges[0]["node"]["inventoryItem"]["id"]
            return cls._parse_gid(gid)
            
        except Exception as e:
            logger.error(f"GraphQL Error for SKU {sku}: {e}")
            return None

    @classmethod
    def update_stock(cls, config, shopify_product, quantity):
        location_id = cls._ensure_location_id(config)
        if not location_id:
            logger.error(f"No location ID found for {config.shop_url}")
            return False

        mutation = """
        mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
          inventorySetQuantities(input: $input) {
            inventoryAdjustmentGroup {
              changes {
                quantityAfterChange
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "name": "available",
                "reason": "correction",
                "ignoreCompareQuantity": True,
                "quantities": [
                    {
                        "inventoryItemId": f"gid://shopify/InventoryItem/{shopify_product.inventory_item_id}",
                        "locationId": f"gid://shopify/Location/{location_id}",
                        "quantity": quantity
                    }
                ]
            }
        }

        url = f"https://{config.shop_url}/admin/api/2024-10/graphql.json"
        headers = {
            "X-Shopify-Access-Token": config.access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json={"query": mutation, "variables": variables}, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Shopify Stock Update Response for {shopify_product.product.sku}: {data}")

            result = data.get("data", {}).get("inventorySetQuantities", {})
            user_errors = result.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Shopify Stock Update Error: {user_errors}")
                return False
                
            return True

        except Exception as e:
            logger.error(f"Stock Update Exception: {e}")
            return False

    @classmethod
    def _ensure_location_id(cls, config):
        if config.location_id:
            return config.location_id

        query = """
        query {
          locations(first: 1) {
            edges {
              node {
                id
              }
            }
          }
        }
        """
        
        url = f"https://{config.shop_url}/admin/api/2024-10/graphql.json"
        headers = {
            "X-Shopify-Access-Token": config.access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json={"query": query}, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            edges = data.get("data", {}).get("locations", {}).get("edges", [])
            if not edges:
                return None
            
            gid = edges[0]["node"]["id"]
            location_id = cls._parse_gid(gid)
            
            config.location_id = location_id
            config.save()
            return location_id
            
        except Exception as e:
            logger.error(f"Error fetching location ID: {e}")
            return None

    @classmethod
    def _parse_gid(cls, gid):
        """
        ID : gid://shopify/InventoryItem/12345678"
        """
        try:
            return int(gid.split("/")[-1])
        except (ValueError, IndexError):
            return None
