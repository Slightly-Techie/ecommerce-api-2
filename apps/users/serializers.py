from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.contrib.auth.password_validation import validate_password

from apps.common.email import send_email_template
from apps.common.utils import OTPUtils
from apps.users.utils import query_community_endpoint

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
        fields = [
            "id",
            "email",
            "username",
            "password",
            "password2",
            "referral_code",
            "member_type",
        ]

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
        member_type = validated_data.get("member_type")
        # Create User
        user = User.objects.create_user(**validated_data)

        # new
        code, _ = OTPUtils.generate_otp(user)
        email = validated_data.get("email")
        username = validated_data.get("username")
        send_email_template(
            email,
            "d-84ad6c792bf64437bb592b604214806a",
            {email: {"username": username, "otp": code}},
        )

        # member type data
        if member_type == "ST":
            member_data = query_community_endpoint(email)
            if not member_data:
                raise serializers.ValidationError(
                    {"email": "Email not found in community database"}
                )

            profile, created = Profile.objects.get_or_create(user=user)
            profile.first_name = member_data["data"]["first_name"]
            profile.last_name = member_data["data"]["last_name"]
            profile.phone_number = member_data["data"]["phone_number"]
            profile.save()

        if referral_code:
            try:
                profile = Profile.objects.get(referral_code=referral_code)
                profile.update_referral(+10)
                user.profile.referrer = profile.user
                user.profile.save(update_fields=["referrer", "updated_at"])
            except Profile.DoesNotExist:
                pass
        return user


# new


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(min_length=6, required=True)

    def create(self, data):
        email = data.get("email")
        code = data.get("code")

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User not found")

        # Verify OTP
        if not OTPUtils.verify_otp(code, user.otp_secret):
            raise serializers.ValidationError("Invalid OTP code")

        # Verify user
        user.is_verified = True
        user.otp_secret = ""
        user.save()

        return user


class SignupResponseSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "token")

    @swagger_serializer_method(
        serializer_or_field=serializers.JSONField(),
    )
    def get_token(self, user: User):  # type: ignore
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

    def validate(self, attrs):
        email = attrs.get("email")
        if not email:
            raise serializers.ValidationError("Email must be provided")
        return attrs

    def create(self, validated_data: dict):
        """
        if email code to a user, send an email with a code to reset password
        """
        token = ""
        email = validated_data.get("email")
        try:
            if user := User.objects.filter(email=email).first():
                code, token = OTPUtils.generate_otp(user)
                user.otp_secret = code
                user.otp_secret_created_at = timezone.now()
                user.save(update_fields=["otp_secret", "otp_secret_created_at"])
                send_email_template(
                    email, "d-45557d1b684442b6aef71ae69d50c495", {email: {"code": code}}
                )
            else:
                raise serializers.ValidationError("User with this email does not exist")
        except Exception as e:
            raise serializers.ValidationError(f"Error sending email: {e}")


        return {"token": token}


class ResetPasswordSerializer(serializers.Serializer):
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

        try:
            data = OTPUtils.decode_token(token)
            if not data or not isinstance(data, dict):
                raise serializers.ValidationError("Invalid token")

            if not (user := User.objects.filter(id=data.get("user_id")).first()):
                raise serializers.ValidationError("User does not exist")

            if not constant_time_compare(user.otp_scret, code):
                raise serializers.ValidationError("Invalid code")

            if user.otp_secret_created_at  + timezone.timedelta(minutes=5) < timezone.now():
                raise serializers.ValidationError("otp code has expired")

            validate_password(password, user)

            # If we get here, verification was successful
            user.set_password(raw_password=password)
            user.otp_scret = None
            user.otp_secret_created_at = None
            user.is_verified = True
            user.save(update_fields=[
                "password",
                "otp_scret",
                "otp_secret_created_at",
                "is_verified"
            ])

            return {"email": user.email}

        except serializers.ValidationError:
            if "user" in locals() and user is not None:
                user.otp_secret = None
                user.otp_secret_created_at  = None
                user.save(update_fields=["otp_scret", "otp_secret_created_at"])
            raise

        except Exception as e:
            if "user" in locals() and user is not None:
                user.otp_secret = None
                user.otp_secret_created_at = None
                user.save(update_fields=["otp_secret", "otp_secret_created_at"])
            raise serializers.ValidationError(f"Password reset failed: {str(e)}")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(min_length=6, required=True)
    new_password = serializers.CharField(min_length=6, required=True)

    class Meta:
        fields = ("old_password", "new_password")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        if not user.check_password(validated_data.get("old_password")):
            raise serializers.ValidationError({"detail": "Incorrect password"})

        # reset password
        user.set_password(raw_password=validated_data.get("new_password"))
        user.save()

        send_email_template(
            user.email,
            "d-7989ffbb4f114616846ef7ddff10a965",
            {user.email: {"username": user.username}},
        )

        return {"old_password": "", "new_password": ""}


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "address_name",
            "street_name",
            "address",
            "city",
            "town",
            "country",
            "lat",
            "lon",
        ]


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
