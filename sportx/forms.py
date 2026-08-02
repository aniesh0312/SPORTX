from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Order
from .models import Review


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer_name",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "pincode",
            "payment_method",
        ]
        widgets = {
            "customer_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your full name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "you@example.com"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "10-digit mobile number"}
            ),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "House number, street and area"}
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "State"}
            ),
            "pincode": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Pincode"}
            ),
            "payment_method": forms.RadioSelect(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "").replace("-", "")
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data["pincode"].strip()
        if not pincode.isdigit() or len(pincode) not in (5, 6):
            raise forms.ValidationError("Enter a valid 5- or 6-digit pincode.")
        return pincode

INPUT_CLASS = "form-control form-control-lg"


class RegisterForm(UserCreationForm):
    """Registration form for Django's built-in User model."""

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Last name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "you@example.com"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "Choose a username", "autocomplete": "username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Create a password", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Confirm your password", "autocomplete": "new-password"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class LoginForm(AuthenticationForm):
    """Styled form that keeps Django's built-in authentication validation."""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASS, "placeholder": "Your username", "autocomplete": "username"}
        )
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": INPUT_CLASS, "placeholder": "Your password", "autocomplete": "current-password"}
        ),
    )


class ProfileForm(UserChangeForm):
    """Allows a signed-in user to update basic account details without changing the password."""

    password = None

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Another account already uses this email address.")
        return email

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
                attrs={"class": "form-select"},
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Review title",
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Share your experience with this product",
                    "rows": 4,
                }
            ),
        }
        