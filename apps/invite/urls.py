from rest_framework.routers import DefaultRouter

from .views import InvitationViewSet

router = DefaultRouter()

router.register(r"invitations", InvitationViewSet, basename="invitation")

urlpatterns = router.urls
