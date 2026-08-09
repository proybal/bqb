# accounts\views.py
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
from .models import Profile

def home_view(request):
    return render(request, 'home')


def signup_view(request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)
        return render(request, 'home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/register.html', {'form': form})


def activation_sent_view(request):
    messages.info(request, 'Activation link sent! Please check your console or mail.')
    return redirect('home')


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
        return render(request, 'accounts/activation_invalid.html')


def registerPage(request):
    if request.user.is_authenticated:
        return redirect("state_news")

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            full_name = HumanName(
                form.cleaned_data["name"]
            )

            user.first_name = full_name.first
            user.last_name = full_name.last
            user.email = form.cleaned_data["email"]
            user.is_active = False
            user.save()

            profile, created = Profile.objects.get_or_create(
                user=user
            )

            profile.first_name = full_name.first
            profile.last_name = full_name.last
            profile.name = form.cleaned_data["name"]
            profile.address = form.cleaned_data.get(
                "address",
                "",
            )

            profile.city = form.cleaned_data.get(
                "city",
                "",
            )

            profile.region = form.cleaned_data.get(
                "region",
                "",
            )

            profile.postal_code = form.cleaned_data.get(
                "postal_code",
                "",
            )
            profile.email = form.cleaned_data["email"]
            profile.phone = form.cleaned_data.get(
                "phone",
                "",
            )
            profile.save()

            current_site = get_current_site(request)

            subject = "Please Activate Your BurqueBro Account"

            message = render_to_string(
                "accounts/activation_request.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(
                        force_bytes(user.pk)
                    ),
                    "token": (
                        account_activation_token
                        .make_token(user)
                    ),
                },
            )

            user.email_user(
                subject,
                message,
                fail_silently=False,
            )

            return redirect("activation_sent")

    else:
        form = SignUpForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )

def loginPage(request):
    if request.user.is_authenticated:
        return redirect("state_news")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            if request.POST.get("remember_me"):
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)

            messages.success(
                request,
                f"Welcome back, {user.username}.",
            )

            next_url = request.POST.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("state_news")

        messages.error(
            request,
            "The username or password is incorrect.",
        )

    return render(
        request,
        "accounts/login.html",
        {
            "next": request.GET.get("next", ""),
        },
    )


def logoutUser(request):
    logout(request)
    return redirect('/home/')

