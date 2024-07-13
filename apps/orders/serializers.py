from rest_framework import serializers

from apps.products.models import Product
from apps.users.models import Address

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "price", "quantity", "order"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')

    class Meta:
        model = Order
        fields = "__all__"