from django import forms

from .models import CafeInquiry, WorkshopInterest


class HoneypotModelForm(forms.ModelForm):
    """Shared, deliberately simple anti-bot field for public forms."""

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
            raise forms.ValidationError("Wykryto automatyczne zgłoszenie.")
        return value

    def full_clean(self):
        """Expose server-side errors to assistive technology."""
        super().full_clean()
        for field_name in self.errors:
            if field_name not in self.fields:
                continue

            error_id = f"id_{field_name}-error"
            attrs = self.fields[field_name].widget.attrs
            described_by = attrs.get("aria-describedby", "").split()
            if error_id not in described_by:
                described_by.append(error_id)
            attrs["aria-describedby"] = " ".join(described_by)
            attrs["aria-invalid"] = "true"


class CafeInquiryForm(HoneypotModelForm):
    PRODUCT_CHOICES = [
        ("shokupan", "Shokupan"),
        ("buns", "Drożdżówki"),
        ("cookies", "Ciastka"),
        ("seasonal_bakes", "Wypieki sezonowe"),
        ("custom_product", "Produkt przygotowany dla lokalu"),
    ]

    interested_products = forms.MultipleChoiceField(
        label="Interesujące produkty",
        choices=PRODUCT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    privacy_consent = forms.BooleanField(
        label=(
            "Zgadzam się na przetwarzanie danych w celu odpowiedzi "
            "na moje zapytanie."
        ),
    )

    class Meta:
        model = CafeInquiry
        fields = [
            "venue_name",
            "contact_name",
            "email",
            "phone",
            "city",
            "interested_products",
            "frequency",
            "message",
            "privacy_consent",
        ]
        widgets = {
            "venue_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "organization"}
            ),
            "contact_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
            "phone": forms.TelInput(
                attrs={"class": "form-control", "autocomplete": "tel"}
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "address-level2"}
            ),
            "frequency": forms.Select(attrs={"class": "form-control"}),
            "message": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }

    def save(self, commit=True):
        inquiry = super().save(commit=False)
        product_labels = dict(self.PRODUCT_CHOICES)
        inquiry.interested_products = ", ".join(
            product_labels[value]
            for value in self.cleaned_data["interested_products"]
        )
        if commit:
            inquiry.save()
        return inquiry


class WorkshopInterestForm(HoneypotModelForm):
    consent_contact = forms.BooleanField(
        label=(
            "Zgadzam się na kontakt w sprawie planowanych warsztatów "
            "i spotkań."
        ),
    )

    class Meta:
        model = WorkshopInterest
        fields = [
            "name",
            "email",
            "topic",
            "preferred_timing",
            "consent_contact",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
            "topic": forms.Select(attrs={"class": "form-control"}),
            "preferred_timing": forms.Select(attrs={"class": "form-control"}),
        }
