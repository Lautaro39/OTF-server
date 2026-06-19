from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("upload/<int:pk>/", views.ProfileUpdateView.as_view(), name="auth-profile-update"),
]
