from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from .models import Inventory
from .serializers import InventorySerializer


class InventoryView(ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAdminUser]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]
