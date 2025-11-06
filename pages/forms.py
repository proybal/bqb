from django import forms


# Create your forms here.

class ContactForm(forms.Form):
    name = forms.CharField(max_length=30, required=False, widget=forms.TextInput
    (attrs={'class': 'form_control',
            'placeholder': 'name'}))
    email_address = forms.EmailField(max_length=150, required=True, widget=forms.EmailInput
    (attrs={'class': 'form_control',
            'placeholder': 'Email address'}))
    message = forms.CharField(max_length=2000, required=True, widget=forms.Textarea
    (attrs={'class': 'form_control',
            'placeholder': 'Message'}))
