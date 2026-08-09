from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        max_length=100,
        label="Username",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
                "autocomplete": "username",
            }
        ),
    )

    name = forms.CharField(
        max_length=100,
        label="Full name",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your full name",
                "autocomplete": "name",
            }
        ),
    )
    address = forms.CharField(
        max_length=100,
        label="Street address",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Street address",
                "autocomplete": "street-address",
            }
        ),
    )

    city = forms.CharField(
        max_length=30,
        label="City",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "City",
                "autocomplete": "address-level2",
            }
        ),
    )

    region = forms.CharField(
        max_length=10,
        label="State",
        required=False,
        initial="NM",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "NM",
                "autocomplete": "address-level1",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=15,
        label="ZIP code",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "87102",
                "autocomplete": "postal-code",
            }
        ),
    )
    phone = forms.CharField(
        max_length=20,
        label="Phone",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "505-555-1212",
                "autocomplete": "tel",
            }
        ),
    )

    email = forms.EmailField(
        max_length=150,
        label="Email address",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a password",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repeat your password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "name",
            "email",
            "phone",
            "address",
            "city",
            "region",
            "postal_code",
            "password1",
            "password2",
        )


    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account already uses this email address."
            )

        return email
