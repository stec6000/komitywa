from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

class EmailOnlySignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)


class AdminUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)


class AdminUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = (
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
