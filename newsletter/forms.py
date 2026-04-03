from django import forms


class NewsletterSignupForm(forms.Form):
    email = forms.EmailField(
        label="Adres email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Twoj adres email",
            }
        ),
    )
    consent_newsletter = forms.BooleanField(
        label=(
            "Wyrazam zgode na otrzymywanie newslettera. "
            '<a href="/polityka-prywatnosci/" target="_blank">'
            "Polityka prywatnosci</a>"
        ),
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )
