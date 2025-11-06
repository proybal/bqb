from django.shortcuts import render, redirect
from .forms import ContactForm
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib import messages


def index(request):
    return render(request, 'pages/index_old.html')


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = "Website Inquiry"
            body = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email_address'],
                'message': form.cleaned_data['message'],
            }
            message = "\n".join(body.values())

            try:
                send_mail(subject, message, 'admin@burquebro.com', ['admin@burquebro.com'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            messages.info(request, "You will be contacted shortly. Thank you. bb")
            return redirect("home")

    form = ContactForm()
    return render(request, "pages/contact.html", {'form': form})