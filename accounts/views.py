# from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.contrib import messages
from nameparser import HumanName
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
# from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect


def home_view(request):
    return render(request, 'index_old.html')
    # return redirect('/news/home/')


def signup_view(request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)
        return render(request, 'home.html')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def activation_sent_view(request):
    # return render(request, 'activation_sent.html')
    messages.info(request, 'Activation link sent! Please check your console or mail.')
    return redirect('home')
    # return render(request, 'pages/index_old.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # checking if the user exists, if the token is valid.
    if user is not None and account_activation_token.check_token(user, token):
        # if valid set active true
        user.is_active = True
        # set signup_confirmation true
        user.profile.signup_confirmation = True
        user.save()
        login(request, user)
        messages.info(request, 'Account Activated.')
        return redirect('home')
    else:
        return render(request, 'activation_invalid.html')


def registerPage(request):
    # if request.user.is_authenticated:
    #     return render(request, 'home.html')
    #
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            name = HumanName(form.cleaned_data.get('name'))
            user.first_name = name.first
            user.last_name = name.last
            user.profile.username = form.cleaned_data.get('username')
            user.profile.first_name = name.first
            user.profile.last_name = name.last
            user.profile.name = name
            user.profile.email = form.cleaned_data.get('email')
            user.profile.address = form.cleaned_data.get('address')
            user.profile.city = form.cleaned_data.get('city')
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Please Activate Your Account'
            # load a template like get_template()
            # and calls its render() method immediately.
            message = render_to_string('activation_request.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                # 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                # method will generate a hash value with user related data
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message, fail_silently=False)
            return redirect('activation_sent')
            # username = form.cleaned_data.get('username')
            # password = form.cleaned_data.get('password1')
            # user = authenticate(username=username, password=password)
            # login(request, user)
            # messages.success(request, 'Account created successfully. Check email to verify the account.')
            # return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('/home/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, 'Welcome ' + username)
                return redirect('/home/')
            else:
                messages.info(request, 'Username OR password is incorrect')
        # return HttpResponseRedirect('/home')
        # return render(request, 'login.html')
        # return render(request, 'index_old.html')
        return redirect('/home/')


def logoutUser(request):
    logout(request)
    return redirect('/home/')
    # return render(request, 'index_old.html')

