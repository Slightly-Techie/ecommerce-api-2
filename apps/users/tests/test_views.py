import pytest
from django.core import mail
from django.urls.base import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User

pytestmark = pytest.mark.django_db


class TestUserView:
    def test_user_list(self, api_client_auth, user: User):
        url = reverse("api:users-list")
        client = api_client_auth(user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "results" in resp_data

    def test_user_read(self, api_client_auth, user: User):
        url = reverse("api:users-detail", args=(user.id,))
        client = api_client_auth(user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["email"] == user.email

    def test_user_update(self, api_client_auth, user: User):
        url = reverse("api:users-detail", args=(user.id,))
        client = api_client_auth(user)
        data = {"email": "a@a.com", "username": "hello_world"}

        resp = client.patch(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["username"] == data["username"]
        assert resp_data["email"] == data["email"]

    def test_me(
        self,
        api_client_auth,
        user: User,
    ):
        url = reverse("api:users-me")
        client = api_client_auth(user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["email"] == user.email


class TestAuthView:
    def test_login(self, api_client: APIClient, user: User, test_password):
        url = reverse("api:token-obtain")
        response = api_client.post(
            url, data={"email": user.email, "password": test_password}
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_with_wrong_credentials(
        self, api_client: APIClient, user: User, test_password
    ):
        url = reverse("api:token-obtain")
        response = api_client.post(
            url, data={"email": user.email, "password": "wrong_password"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_signup(self, api_client: APIClient, test_password, test_email):
        url = reverse("api:signup")
        data = {
            "email": test_email,
            "username": "test_name",
            "password": test_password,
            "password2": test_password,
        }
        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED

        assert len(mail.outbox) == 0

    def test_refresh_token(self, api_client: APIClient, user: User, token: dict):
        url = reverse("api:token-refresh")

        data = {"refresh": token["refresh"]}
        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK

    def test_change_password(self, api_client_auth, user, test_password):
        url = reverse("api:change-password")
        client = api_client_auth(user=user)
        data = {"old_password": test_password, "new_password": "new_password"}
        resp = client.post(url, data=data)

        assert resp.status_code == status.HTTP_201_CREATED

    def test_change_password_wrong_password(self, api_client_auth, user, test_password):
        url = reverse("api:change-password")
        client = api_client_auth(user=user)
        data = {"old_password": "wrong_password", "new_password": "new_password"}
        resp = client.post(url, data=data)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_forget_password(self, api_client, user):
        url = reverse("api:forget-password")

        resp = api_client.post(url, data={"email": user.email})
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "token" in resp_data
        assert len(mail.outbox) == 1

    def test_forget_password_wrong_email(self, api_client, user):
        url = reverse("api:forget-password")

        resp = api_client.post(url, data={"email": "a@a.com"})
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "token" in resp_data
        assert len(mail.outbox) == 0

    def test_reset_password(self, api_client, otp_code, test_password):
        code, token = otp_code
        url = reverse("api:reset-password")
        data = {"token": token, "code": code, "password": test_password}
        resp = api_client.post(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "message" in resp_data

    def test_reset_password_wrong_code(self, api_client, otp_code, test_password):
        _, token = otp_code
        url = reverse("api:reset-password")
        data = {"token": token, "code": "000000", "password": test_password}
        resp = api_client.post(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid code" in resp_data

    def test_reset_password_wrong_token(
        self, api_client, otp_code, wrong_otp_token, test_password
    ):
        code, _ = otp_code
        url = reverse("api:reset-password")
        data = {"token": wrong_otp_token, "code": code, "password": test_password}
        resp = api_client.post(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in resp_data


class TestRole:
    def test_create_role(self, api_client_auth, admin_user):
        url = reverse("api:role-list")
        client = api_client_auth(user=admin_user)
        data = {"name": "Backend"}

        resp = client.post(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp_data["name"] == data["name"]

    def test_list_role(self, api_client, role_factory):
        url = reverse("api:role-list")

        role_factory.create_batch(2)

        resp = api_client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert len(resp_data["results"]) == 2

    def test_read_role(self, api_client, role_factory):
        role = role_factory()
        url = reverse("api:role-detail", args=(role.id,))

        resp = api_client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["name"] == role.name

    def test_update_role(self, api_client_auth, admin_user, role_factory):
        role = role_factory()
        url = reverse("api:role-detail", args=(role.id,))
        data = {"name": "Backend"}

        client = api_client_auth(user=admin_user)
        resp = client.patch(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["name"] == data["name"]


class TestAddress:
    def test_list_address(self, api_client_auth, admin_user, address_factory):
        url = reverse("api:address-list")
        address_factory.create_batch(3)

        client = api_client_auth(user=admin_user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert len(resp_data["results"]) == 3

    def test_create_address(self, api_client_auth, user):
        url = reverse("api:address-list")
        client = api_client_auth(user=user)
        data = {
            "user": user.id,
            "address_name": "Home address",
            "address": "addres location",
        }

        resp = client.post(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp_data["address_name"] == data["address_name"]

    def test_update_address(self, api_client_auth, admin_user, address_factory):
        address = address_factory()
        url = reverse("api:address-detail", args=(address.id,))
        data = {"address_name": "Updated name"}

        client = api_client_auth(user=admin_user)
        resp = client.patch(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["address_name"] == data["address_name"]

    def test_read_address(self, api_client_auth, admin_user, address_factory):
        address = address_factory()
        url = reverse("api:address-detail", args=(address.id,))

        client = api_client_auth(user=admin_user)
        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["address_name"] == address.address_name


class TestProfile:
    def test_list_profile(self, api_client_auth, admin_user, user):
        url = reverse("api:profile-list")

        client = api_client_auth(user=admin_user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert len(resp_data["results"]) == 2

    def test_update_profile(self, api_client_auth, admin_user, user):
        url = reverse("api:profile-detail", args=(user.profile.id,))
        client = api_client_auth(user=admin_user)
        data = {"gender": "f"}

        resp = client.patch(url, data=data)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["gender"] == data["gender"]

    def test_read_profile(self, api_client_auth, user):
        url = reverse("api:profile-detail", args=(user.profile.id,))

        client = api_client_auth(user=user)

        resp = client.get(url)
        resp_data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert resp_data["user"] == str(user.id)
