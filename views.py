from django.shortcuts import render, redirect
from .forms import ContactForm
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse


def index(request):
    # return render(request, 'home.html')
    return render(request, 'pages/index.html')


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
                send_mail(subject, message, 'proybal@yahoo.com', ['proybal@yahoo.com'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            messages.info(request, "You will be contacted shortly. Thank you. bb")
            return redirect("home")

    form = ContactForm()
    return render(request, "pages/contact.html", {'form': form})