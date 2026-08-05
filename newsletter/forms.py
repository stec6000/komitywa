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
            "Wyrażam zgodę na otrzymywanie Listów z Komitywy. "
            '<a href="/polityka-prywatnosci/" target="_blank">'
            "Polityka prywatności</a>"
        ),
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )
    # Honeypot — boty często wypełniają pola o nazwie "website".
    # Human users go nie widzą (ukryte przez CSS .kk-honeypot).
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "kk-honeypot",
                "autocomplete": "off",
                "tabindex": "-1",
                "aria-hidden": "true",
            }
        ),
    )

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("bot-detected")
        return value
