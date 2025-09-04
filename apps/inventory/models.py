from django.db import models

from apps.common import models as base_models
from apps.products.models import Product


class Inventory(base_models.BaseModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = "inventories"
        ordering = ("created_at",)

    def __str__(self):
        return f"There are {self.quantity} units of {self.product.name} available"
