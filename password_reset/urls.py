# type: ignore

# password_reset/urls.py
from django.urls import path
from . import views

app_name = 'password_reset'

urlpatterns = [
    path('request/', views.PasswordResetRequestView.as_view(), name='request'),
    path('verify/', views.PasswordResetVerifyView.as_view(), name='verify'),
    path('confirm/', views.PasswordResetConfirmView.as_view(), name='confirm'),
    path('status/', views.PasswordResetStatusView.as_view(), name='status'),
]