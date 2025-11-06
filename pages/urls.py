from django.urls import path
from django.conf.urls import url

import accounts.views

from . import views

urlpatterns = [
    # path('', views.index, name='home'),
    # path('home/', views.index, name='home'),
    # path('home/', views.index, name='home'),
    path('signup/', accounts.views.signup_view, name="signup"),
    path('register/', accounts.views.registerPage, name="register"),
    path('login/', accounts.views.loginPage, name="login"),
    path('logout/', accounts.views.logoutUser, name="logout"),
    path('sent/', accounts.views.activation_sent_view, name="activation_sent"),
    path('activate/<slug:uidb64>/<slug:token>/', accounts.views.activate, name='activate'),
    path("contact", views.contact, name="contact"),
    path("about", views.about, name="about")
]
