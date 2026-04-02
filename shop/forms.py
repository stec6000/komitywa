from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Adres email")
    name = forms.CharField(max_length=200, label="Imie i nazwisko")
    phone = forms.CharField(
        max_length=20, required=False, label="Telefon (opcjonalnie)"
    )
    pickup_date = forms.CharField(
        max_length=100,
        label="Preferowana data odbioru",
        help_text="np. piatek 10 stycznia, godziny popoludniowe",
    )
    consent_data = forms.BooleanField(
        label="Wyrazam zgode na przetwarzanie moich danych osobowych "
        "w celu realizacji zamowienia"
    )
    consent_terms = forms.BooleanField(
        label="Akceptuje regulamin sklepu"
    )
