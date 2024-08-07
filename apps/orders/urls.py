from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderItemViewset, OrderViewSet

router = DefaultRouter()

router.register("item", OrderItemViewset, basename="order_item")
router.register("", OrderViewSet, basename="order")

# urlpatterns = router.urls
urlpatterns = [
    path("", include(router.urls)),
    path(
        "payment/verify/",
        OrderViewSet.as_view({"get": "payment_verify"}),
        name="order-payment_verify",
    ),
]
