from django import forms
from django.utils.safestring import mark_safe

from .models import OrderEdition, RzutItem, RzutOrder


def pickup_slot_value(slot):
    return f"{slot.starts_at.isoformat()}|{slot.ends_at.isoformat()}"


def pickup_slot_label(slot):
    return (
        f"{slot.starts_at.strftime('%H:%M')}–"
        f"{slot.ends_at.strftime('%H:%M')}"
    )


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
            pickup_slot_value(slot): slot for slot in rzut.pickup_slots()
        }
        self.fields["pickup_slot"].choices = [
            (value, pickup_slot_label(slot))
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

class ManualRzutChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        pickup_date = (
            obj.pickup_date.strftime("%d.%m.%Y")
            if obj.pickup_date
            else "bez daty odbioru"
        )
        return f"{obj.title} — {pickup_date} — {obj.get_status_display()}"


class ManualRzutOrderAdminForm(forms.Form):
    creation_token = forms.UUIDField(widget=forms.HiddenInput)
    rzut = ManualRzutChoiceField(
        queryset=OrderEdition.objects.order_by("-pickup_date", "-created_at"),
        label="Rzut",
    )
    customer_name = forms.CharField(max_length=200, label="Imię i nazwisko")
    customer_email = forms.EmailField(max_length=50, label="E-mail Klienta")
    customer_phone = forms.CharField(
        max_length=30,
        required=False,
        label="Telefon",
    )
    customer_notes = forms.CharField(
        max_length=500,
        required=False,
        label="Uwagi Klienta",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    pickup_slot = forms.ChoiceField(label="Przedział Odbioru")
    payment_status = forms.ChoiceField(
        choices=RzutOrder.PaymentStatus.choices,
        label="Status Płatności",
    )
    payment_method = forms.ChoiceField(
        choices=RzutOrder.PaymentMethod.choices,
        label="Metoda Płatności",
    )
    payment_method_details = forms.CharField(
        max_length=200,
        required=False,
        label="Wyjaśnienie Metody Płatności",
        help_text="Wymagane dla Metody Płatności „inna”.",
    )
    discount_code = forms.CharField(
        max_length=50,
        required=False,
        label="Kod Rabatowy",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rzut_id = None
        if self.is_bound:
            rzut_id = self.data.get("rzut")
        elif self.initial:
            rzut_id = self.initial.get("rzut")
        self._rzut = OrderEdition.objects.filter(pk=rzut_id).first()
        self._pickup_slots = {}
        self.rzut_items = []
        if self._rzut is None:
            self.fields["pickup_slot"].choices = []
            self.fields["pickup_slot"].help_text = (
                "Najpierw wybierz Rzut."
            )
        else:
            self._pickup_slots = {
                pickup_slot_value(slot): slot
                for slot in self._rzut.pickup_slots()
            }
            self.fields["pickup_slot"].choices = [
                (value, pickup_slot_label(slot))
                for value, slot in self._pickup_slots.items()
            ]
            self.rzut_items = list(
                RzutItem.objects.filter(
                    rzut=self._rzut,
                    is_active=True,
                    product__type="physical",
                )
                .select_related("product")
                .order_by("sort_order", "product__title")
            )
        for item in self.rzut_items:
            self.fields[self.quantity_field_name(item)] = forms.IntegerField(
                min_value=0,
                required=False,
                initial=0,
                label=(
                    f"{item.product.title} — {item.portion} "
                    f"({item.price:.2f} zł; dostępne: "
                    f"{item.available_quantity})"
                ),
            )
        self.item_rows = [
            (item, self[self.quantity_field_name(item)])
            for item in self.rzut_items
        ]
        self.customer_fields = [
            self[name]
            for name in [
                "customer_name",
                "customer_email",
                "customer_phone",
                "customer_notes",
                "pickup_slot",
            ]
        ]
        self.settlement_fields = [
            self[name]
            for name in [
                "payment_status",
                "payment_method",
                "payment_method_details",
                "discount_code",
            ]
        ]

    def clean_customer_email(self):
        return self.cleaned_data["customer_email"].strip().casefold()

    def clean_pickup_slot(self):
        value = self.cleaned_data["pickup_slot"]
        try:
            return self._pickup_slots[value]
        except KeyError as exc:
            raise forms.ValidationError(
                "Wybierz dostępny Przedział Odbioru."
            ) from exc

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get("payment_method")
        details = cleaned_data.get("payment_method_details", "").strip()
        if method == RzutOrder.PaymentMethod.OTHER and not details:
            self.add_error(
                "payment_method_details",
                "Wyjaśnij inną Metodę Płatności.",
            )

        if self._rzut is not None and not self._pickup_slots:
            raise forms.ValidationError(
                "Wybrany Rzut nie ma dostępnych Przedziałów Odbioru. "
                "Najpierw uzupełnij godziny odbioru w Rzucie."
            )
        if self._rzut is not None and not self.rzut_items:
            raise forms.ValidationError(
                "Wybrany Rzut nie ma aktywnych fizycznych Pozycji Rzutu. "
                "Najpierw uzupełnij jego ofertę."
            )

        self.cleaned_lines = []
        for item in self.rzut_items:
            quantity = cleaned_data.get(self.quantity_field_name(item)) or 0
            if quantity > 0:
                self.cleaned_lines.append((item.pk, quantity))
        if self.rzut_items and not self.cleaned_lines:
            raise forms.ValidationError(
                "Podaj liczbę sztuk co najmniej jednej Pozycji Rzutu."
            )
        return cleaned_data

    @property
    def selected_rzut(self):
        return self._rzut

    @property
    def has_pickup_slots(self):
        return bool(self._pickup_slots)

    @property
    def has_rzut_items(self):
        return bool(self.rzut_items)

    @property
    def can_submit(self):
        return (
            self._rzut is not None
            and self.has_pickup_slots
            and self.has_rzut_items
        )

    @staticmethod
    def quantity_field_name(item):
        return f"quantity_{item.pk}"
