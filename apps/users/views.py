from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import Address, Profile, Role
from .serializers import (
    AddressSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ProfileSerializer,
    ResetPasswordSerializer,
    RoleSerializer,
    SignupResponseSerializer,
    SignUpSerializer,
    UserSerializer,
)

User = get_user_model()


response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "message": openapi.Schema(type=openapi.TYPE_STRING),
    },
)

forget_password_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"token": openapi.Schema(type=openapi.TYPE_STRING)},
)


class UserView(RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    """
    User viewset
    """

    serializer_class = UserSerializer
    queryset = User.objects.all()
    filterset_fields = ["is_active", "deleted"]
    search_fields = [
        "email",
        "name",
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.none()
        return self.queryset.filter(id=user.id)

    @swagger_auto_schema(method="GET", responses={200: UserSerializer})
    @action(detail=False, methods=["GET"])
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class SignUpView(CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="User signup", responses={201: SignupResponseSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_serializer = SignupResponseSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ForgotPasswordView(CreateAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={200: forget_password_schema})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return Response(data, status=status.HTTP_200_OK)


class ResetPasswordView(CreateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={200: response_schema})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password set succesfully"}, status=status.HTTP_200_OK
        )


class ChangePasswordView(CreateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]


class RoleView(ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AllowAny]

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class AddressView(ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.none()
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)


class ProfileView(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    filterset_fields = ("user", "role")
    parser_classes = (FormParser, MultiPartParser)

    http_method_names = [m for m in ModelViewSet.http_method_names if m not in ["put"]]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.none()
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)
