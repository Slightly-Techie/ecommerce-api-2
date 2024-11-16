from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Inventory
from .serializers import InventorySerializer


class InventoryView(ReadOnlyModelViewSet):
    queryset = Inventory.objects.all().select_related("product")
    serializer_class = InventorySerializer
    permission_classes = [IsAdminUser]

    # http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]
