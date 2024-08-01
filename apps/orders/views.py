from django.db import transaction
from django.shortcuts import get_object_or_404

# from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.cart.models import CartItem, ShoppingCart
from apps.finance.models import Transaction
from apps.finance.paystack import PaystackUtils
from apps.orders.models import Order, OrderItem
from apps.orders.serializers import OrderItemSerializer, OrderSerializer
from apps.users.models import Address


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer

    http_method_names = [
        m for m in ModelViewSet.http_method_names if m not in ["put", "patch"]
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user)
        return Order.objects.none()

    @action(detail=False, methods=["post"], url_path="checkout")
    @transaction.atomic
    def checkout(self, request):
        cart = ShoppingCart.objects.filter(user=request.user).first()
        if not cart:
            return Response(
                {"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )
        cart_items = CartItem.objects.filter(cart=cart.id)

        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        delivery_cost = 10
        total_cost = total_amount + delivery_cost
        user_address = Address.objects.filter(user=request.user).first()

        order = Order.objects.create(
            user=request.user,
            delivery_cost=delivery_cost,
            total_cost=total_cost,
            delivery_address=user_address,
            status="PE",
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price,
            )

        serializer = self.get_serializer(order)  # noqa

        kobo_amount = int(total_cost * 1000)
        # callback_url = request.build_absolute_uri(reverse("payment_verify"))
        callback_url = request.build_absolute_uri(
            "http://127.0.0.1:8000/api/order/payment/verify/"
        )
        # callback_url = reverse("payment_verify")

        payment_response = PaystackUtils.initialize_transaction(
            amount=kobo_amount,
            email=request.user.email,
            callback_url=callback_url,
            reference=str(order.id),
        )

        if payment_response["status"]:
            return Response(
                {
                    "order_id": order.id,
                    "payment_url": payment_response["data"]["authorization_url"],
                }
            )
        else:
            order.delete()
            return Response({"details": "Failed to initialize payment"})

    @action(
        detail=False,
        methods=["get"],
        url_path="payment/verify",
        url_name="payment_verify",
    )
    def payment_verify(self, request):
        reference = request.query_params.get("reference")

        if not reference:
            return Response(
                {"detail": " No reference provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        response = PaystackUtils.verify_transaction(reference)

        if response["status"]:
            if response["data"]["status"] == "success":
                order = get_object_or_404(Order, id=reference)
                order.status = "PC"
                order.save()

                Transaction.objects.create(
                    user=request.user,
                    order=order,
                    amount=order.total_cost,
                    status="PA",
                    payment_method="CD",
                )

                ShoppingCart.objects.filter(user=request.user).delete()

                return Response(
                    {"detail": "Payment successful"}, status=status.HTTP_200_OK
                )

            else:
                return Response(
                    {"detail": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(
                {"detail": "Failed to verify payment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # @action(detail=True, methods=["post"])
    # @transaction.atomic
    # def process_payment(self, request, pk=None):
    #     order = self.get_object()

    #     success = True  # I simulated the payment gateway integration

    #     if success:
    #         Transaction.objects.create(
    #             user=request.user,
    #             order=order,
    #             amount=order.total_cost,
    #             status="PA",
    #             payment_method="CD",
    #         )

    #         order.status = "PC"
    #         order.save()

    #         return Response({"detail": "Payment successful"}, status=status.HTTP_200_OK)
    #     else:
    #         return Response(
    #             {"detail": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST
    #         )


class OrderItemViewset(ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    http_method_names = [
        m
        for m in ModelViewSet.http_method_names
        if m not in ["put", "patch", "post", "delete"]
    ]

    def list(self, request, *args, **kwargs):
        order_id = self.request.query_params.get("order_id")
        queryset = self.get_queryset()
        if order_id:
            queryset = self.queryset.filter(order_id=order_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
