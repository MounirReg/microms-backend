from django.core.management.base import BaseCommand
from business.shopify_orders import ShopifyOrderService

class Command(BaseCommand):
    help = 'Sync orders for all active shopify configs'

    def handle(self, *args, **options):
        self.stdout.write("Starting synchronization...")
        
        results = ShopifyOrderService.sync_all_active_shops()
        
        if not results:
             self.stdout.write(self.style.WARNING("No active shops found or empty results."))
             return

        for shop, stats in results.items():
            if "error" in stats:
                self.stdout.write(self.style.ERROR(f"[{shop}] Error: {stats['error']}"))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[{shop}] Created: {stats['created']}, Updated: {stats['updated']}"
                ))