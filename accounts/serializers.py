from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email

from dj_rest_auth.serializers import LoginSerializer


class EmailOnlyRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_account_settings.UNIQUE_EMAIL:
            if email and EmailAddress.objects.is_verified(email):
                raise serializers.ValidationError(
                    _("User is already registered with this e-mail address.")
                )
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                _("User is already registered with this e-mail address.")
            )
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(
                {"password2": _("The two password fields didn't match.")}
            )
        return data

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user = adapter.save_user(request, user, self, commit=False)
        if "password1" in self.cleaned_data:
            try:
                adapter.clean_password(self.cleaned_data["password1"], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    detail=serializers.as_serializer_error(exc)
                )
        user.save()
        setup_user_email(request, user, [])
        return user


class EmailOnlyLoginSerializer(LoginSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
