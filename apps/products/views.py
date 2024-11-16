from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Favorite, Product, ProductCategory, ProductImage
from .serializers import (
    FavoriteSerializer,
    ProductCategorySerializer,
    ProductImageSerializer,
    ProductSerializer,
)


class ProductCategoryView(ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class ProductView(ModelViewSet):
    queryset = Product.objects.all().select_related("brand", "category")
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class ProductImageView(ModelViewSet):
    queryset = ProductImage.objects.all().select_related("product")
    serializer_class = ProductImageSerializer
    permission_classes = [AllowAny]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class FavoriteView(ModelViewSet):
    queryset = Favorite.objects.all().select_related("product", "user")
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.none()
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)
