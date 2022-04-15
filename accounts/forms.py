from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('name', 'first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2',)

    username = forms.CharField(max_length=100, help_text='Name', required=True, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'User name'}))
    name = forms.CharField(max_length=100, help_text='User Name', required=True, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'Full name'}))
    first_name = forms.CharField(max_length=30, help_text='First Name', required=False, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, help_text='Last Name', required=False, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'Last name'}))
    phone = forms.CharField(max_length=20, help_text='Phone', required=False, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'Phone'}))
    email = forms.EmailField(max_length=150, help_text='Email', required=True, widget=forms.EmailInput
    (attrs={'class': 'form_control',
            'placeholder': 'Email address'}))
    password1 = forms.CharField(max_length=20, help_text='Password', required=True, widget=forms.PasswordInput
    (attrs={'class': 'form_control',
            'placeholder': 'Password'}))
    password2 = forms.CharField(max_length=20, help_text='Repeat password', required=True, widget=forms.PasswordInput
    (attrs={'class': 'form_control',
            'placeholder': 'Repeat password'}))
