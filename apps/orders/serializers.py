from rest_framework import serializers

from .models import Delivery, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "price", "quantity", "order"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source="orderitem_set")

    class Meta:
        model = Order
        fields = "__all__"


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            "id",
            "order",
            "tracking_id",
            "delivery_date",
            "delivery_type",
            "address",
        ]
