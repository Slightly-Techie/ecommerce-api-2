from django.db import models

from apps.common import models as base_models


class ProductCategory(base_models.BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return self.name
