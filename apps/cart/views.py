from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.cart.models import CartItem, ShoppingCart
from apps.cart.serializers import (
    AddToCartSerializer,
    CartItemSerializer,
    ShoppingCartSerializer,
)


class ShoppingCartViewSet(ModelViewSet):
    serializer_class = ShoppingCartSerializer

    http_method_names = [
        m for m in ModelViewSet.http_method_names if m not in ["put", "patch"]
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=self.request.user).select_related(
                "items__product", "items__product__brand", "items__product__category"
            )
        return ShoppingCart.objects.none()

    def get_object(self):
        user = self.request.user
        if user.is_authenticated:
            obj, created = ShoppingCart.objects.get_or_create(user=self.request.user)
            return obj

    def get_serializer_class(self):
        if self.action == "add_to_cart":
            self.serializer_class = AddToCartSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["post"], url_path="add")
    def add_to_cart(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data.get("product")
        quantity = serializer.validated_data.get("quantity")

        cart = self.get_object()

        cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = quantity
        cart_item.price = product.price * quantity
        cart_item.save()

        response_data = CartItemSerializer(cart_item)
        return Response(response_data.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="cartitem/(?P<item_id>[^/.]+)")
    def retrieve_cartitem(self, request, item_id=None):
        try:
            cart_item = CartItem.objects.select_related("product").get(id=item_id)

        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except CartItem.MultipleObjectsReturned:
            return Response({"detail": "Multiple Items found"})

        response_data = CartItemSerializer(cart_item)
        return Response(response_data.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["delete"], url_path="remove/(?P<item_id>[^/.]+)")
    def remove_from_cart(self, request, item_id=None):
        try:
            cart_item = CartItem.objects.get(id=item_id)

        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except CartItem.MultipleObjectsReturned:
            return Response({"detail": "Multiple items found"})

        cart_item.delete()

        return Response(
            {"message": "Item removed successfully"}, status=status.HTTP_204_NO_CONTENT
        )
