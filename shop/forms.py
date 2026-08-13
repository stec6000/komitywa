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


class RzutCheckoutForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        label="Imię i nazwisko",
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "name"}
        ),
    )
    email = forms.EmailField(
        max_length=50,
        label="Adres e-mail",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "autocomplete": "email"}
        ),
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        label="Telefon (opcjonalnie)",
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "tel"}
        ),
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        label="Krótkie uwagi (opcjonalnie)",
        help_text=(
            "Uwagi nie gwarantują zmiany składu ani modyfikacji "
            "alergicznych. W takiej sprawie skontaktuj się z nami przed "
            "złożeniem zamówienia."
        ),
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        ),
    )
    pickup_slot = forms.ChoiceField(
        label="Przedział Odbioru",
        help_text="To orientacyjna godzina odbioru, bez osobnego limitu.",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    consent_data = forms.BooleanField(
        label=(
            "Wyrażam zgodę na przetwarzanie moich danych osobowych "
            "w celu realizacji zamówienia"
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    consent_terms = forms.BooleanField(
        label=mark_safe(
            'Akceptuję <a href="/regulamin/" target="_blank">'
            "regulamin sklepu</a>"
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, rzut, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pickup_slots = {
            self._slot_value(slot): slot for slot in rzut.pickup_slots()
        }
        self.fields["pickup_slot"].choices = [
            (value, self._slot_label(slot))
            for value, slot in self._pickup_slots.items()
        ]

    def clean_email(self):
        return self.cleaned_data["email"].strip().casefold()

    def clean_pickup_slot(self):
        value = self.cleaned_data["pickup_slot"]
        try:
            return self._pickup_slots[value]
        except KeyError as exc:
            raise forms.ValidationError(
                "Wybierz dostępny Przedział Odbioru."
            ) from exc

    @staticmethod
    def _slot_value(slot):
        return f"{slot.starts_at.isoformat()}|{slot.ends_at.isoformat()}"

    @staticmethod
    def _slot_label(slot):
        return (
            f"{slot.starts_at.strftime('%H:%M')}–"
            f"{slot.ends_at.strftime('%H:%M')}"
        )
