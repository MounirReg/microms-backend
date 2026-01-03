from django.contrib import admin
from domain.models import Product, Order, OrderLine, Address, ShopifyConfig

class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'reference', 'customer_email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['reference', 'customer_email']
    inlines = [OrderLineInline]

admin.site.register(Product)
admin.site.register(Address)
admin.site.register(ShopifyConfig)