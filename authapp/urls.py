# type: ignore
# authapp/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authapp'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('google-signup/', views.GoogleSignUpView.as_view(), name='google_signup'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('google-login/', views.GoogleLoginView.as_view(), name='google_login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('check-email/', views.CheckEmailView.as_view(), name='check_email'),
    
    # JWT token endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
    
    # User stats and dashboard
    path('stats/', views.UserStatsView.as_view(), name='user_stats'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
]