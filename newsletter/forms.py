from django import forms


class NewsletterSignupForm(forms.Form):
    email = forms.EmailField(
        label="Adres email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Twój adres email",
            }
        ),
    )
    consent_newsletter = forms.BooleanField(
        label=(
            "Wyrażam zgodę na otrzymywanie newslettera. "
            '<a href="/polityka-prywatnosci/" target="_blank">'
            "Polityka prywatności</a>"
        ),
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )
