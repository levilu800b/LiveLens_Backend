# type: ignore

# password_reset/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('verify/', views.PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]