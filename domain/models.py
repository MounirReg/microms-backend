from django.db import models

class Product(models.Model):
    sku = models.CharField(max_length=20)
    name = models.CharField(max_length=40)
    physical_stock = models.IntegerField()
    available_stock = models.IntegerField()
    pictureUrl = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sku

class Address(models.Model):
    name = models.CharField(max_length=100)
    street = models.TextField()
    postal_code = models.CharField(max_length=20)
    country_code = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.name}, {self.postal_code}"

class Order(models.Model):
    class Status(models.TextChoices):
        WAITING_PAYMENT = 'WAITING_PAYMENT', 'Waiting Payment'
        TO_BE_PREPARED = 'TO_BE_PREPARED', 'To Be Prepared'
        SHIPPED = 'SHIPPED', 'Shipped'
        CANCELED = 'CANCELED', 'Canceled'
        ERROR = "ERROR", "Error"

    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    reference = models.CharField(max_length=50, unique=True)
    customer_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING_PAYMENT,
    )

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"

class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.sku}"

class ShopifyConfig(models.Model):
    shop_url = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    location_id = models.BigIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_url
    
class ShopifyProduct(models.Model):
    config = models.ForeignKey(ShopifyConfig, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    inventory_item_id = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['config', 'product'],
                name='unique_shopify_product_link'
            )
        ]

class ShopifyOrder(models.Model):
    config = models.ForeignKey(ShopifyConfig, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shopify_order_id = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['config', 'order'],
                name='unique_shopify_order_link'
            )
        ]
