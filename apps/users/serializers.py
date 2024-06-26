from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.email import send_email
from apps.common.utils import OTPUtils

from .models import Address, Profile, Role

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    """
    serializer for signing up a new user
    """

    password = serializers.CharField(min_length=6, write_only=True)
    password2 = serializers.CharField(min_length=6, write_only=True)
    referral_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "password2", "referral_code"]

    # Check if passwords match
    def validate_password2(self, password2: str):
        if self.initial_data.get("password") != password2:
            raise serializers.ValidationError("passwords do not match")
        return password2

    def validate(self, attrs):
        """
        Take out referral_code to ensure validation does not fail.
        This is because we dont have referral_code field on user Model
        """
        referral_code = attrs.pop("referral_code", None)
        attrs = super().validate(attrs)

        # Add referral code back to attrs
        attrs["referral_code"] = referral_code
        return attrs

    def create(self, validated_data: dict):
        # Remove second password field
        _ = validated_data.pop("password2")
        referral_code = validated_data.pop("referral_code", None)
        # Create User
        user = User.objects.create_user(**validated_data)

        if referral_code:
            try:
                profile = Profile.objects.get(referral_code=referral_code)
                profile.update_referral(5)
                user.profile.referrer = profile.user
                user.profile.save(update_fields=["referrer", "updated_at"])
            except Profile.DoesNotExist:
                pass
        return user


class SignupResponseSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "token")

    @swagger_serializer_method(
        serializer_or_field=serializers.JSONField(),
    )
    def get_token(self, user: User):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "id"]


class ForgotPasswordSerializer(serializers.Serializer):
    """
    serializer for initiating forgot password. Send reset code
    """

    email = serializers.EmailField(required=True)

    def create(self, validated_data: dict):
        """
        if email code to a user, send an email with a code to reset password
        """
        token = ""
        email = validated_data.get("email")
        if user := User.objects.filter(email=email).first():
            code, token = OTPUtils.generate_otp(user)

            # dynamic_data = {"first_name": user.first_name, "verification_code": code}
            send_email(email, "Password Reset", code)

        return {"token": token}


class ResetPasswordSerializer(serializers.Serializer):
    """ """

    token = serializers.CharField(required=True)
    code = serializers.CharField(min_length=6, required=True)
    password = serializers.CharField(min_length=6, required=True)

    def create(self, validated_data):
        """
        reset user password using email as an identification
        """

        token = validated_data.get("token")
        code = validated_data.get("code")
        password = validated_data.get("password")

        data = OTPUtils.decode_token(token)

        if not data or not isinstance(data, dict):
            raise serializers.ValidationError("Invalid token")

        if not (user := User.objects.filter(id=data.get("user_id")).first()):
            raise serializers.ValidationError("User does not exist")

        # validate code
        if not OTPUtils.verify_otp(code, data["secret"]):
            raise serializers.ValidationError("Invalid code")

        # reset password
        user.set_password(raw_password=password)
        user.save()

        return {
            "email": user.email,
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(min_length=6, required=True)
    new_password = serializers.CharField(min_length=6, required=True)

    class Meta:
        fields = ("old_password", "new_password")

    def create(self, validated_data):
        request = self.context.get("request")
        user: User = request.user

        if not user.check_password(validated_data.get("old_password")):
            raise serializers.ValidationError({"detail": "Incorrect password"})

        # reset password
        user.set_password(raw_password=validated_data.get("new_password"))
        user.save()

        return {"old_password": "", "new_password": ""}


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    address_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "role",
            "role_name",
            "address",
            "address_name",
            "gender",
            "dob",
            "phone_number",
            "profile_image",
        )

    def get_email(self, profile) -> str:
        return profile.user.email if profile.user else ""

    def get_role_name(self, profile) -> str:
        return profile.role.name if profile.role else ""

    def get_address_name(self, profile) -> str:
        return profile.address.address_name if profile.address else ""
