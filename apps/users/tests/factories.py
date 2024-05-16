from typing import Any, Sequence

import factory
from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from apps.users.models import Address, Profile, Role


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    username = Faker("word")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["email"]


class RoleFactory(DjangoModelFactory):
    name = Faker("name")

    class Meta:
        model = Role
        django_get_or_create = ("name",)


class AddressFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Address


class ProfileFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    address = factory.SubFactory(AddressFactory)

    class Meta:
        model = Profile
