from django import forms
from django.utils.safestring import mark_safe


class CheckoutForm(forms.Form):
    email = forms.EmailField(
        label="Adres email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    name = forms.CharField(
        max_length=200,
        label="Imię i nazwisko",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon (opcjonalnie)",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pickup_date = forms.CharField(
        max_length=100,
        required=False,
        label="Preferowana data odbioru",
        help_text="np. piątek 10 stycznia, godziny popołudniowe",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    consent_data = forms.BooleanField(
        label="Wyrażam zgodę na przetwarzanie moich danych osobowych "
        "w celu realizacji zamówienia",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    consent_terms = forms.BooleanField(
        label=mark_safe(
            'Akceptuję <a href="/regulamin/" target="_blank">regulamin sklepu</a>'
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
