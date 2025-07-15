from cloudinary.models import CloudinaryField
from django.db import models

from apps.brands.models import Brand
from apps.common import models as base_models
from apps.users.models import User


class ProductCategory(base_models.BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(base_models.BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    specification = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)

    class Meta:
        ordering = (
            "is_active",
            "updated_at",
            "created_at",
        )

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            from apps.inventory.models import Inventory

            Inventory.objects.create(product=self, quantity=1)

    def __str__(self):
        return self.name


class ProductImage(base_models.BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # product_image = models.ImageField(upload_to="Product_Img")
    product_image = CloudinaryField("image")

    class Meta:
        ordering = ("created_at",)


class Favorite(base_models.BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="favorites"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.user.username} added {self.product} to favorites"
