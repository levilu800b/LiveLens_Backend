# type: ignore
# authapp/urls.py


from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    path('google-auth/', views.google_auth, name='google-auth'),
    
    # Token management
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User profile management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete-account'),
    
    # User library and favorites
    path('library/', views.UserLibraryView.as_view(), name='user-library'),
    path('library/<int:pk>/', views.UserLibraryDetailView.as_view(), name='user-library-detail'),
    path('favorites/', views.UserFavoritesView.as_view(), name='user-favorites'),
    path('favorites/<int:pk>/', views.UserFavoritesDetailView.as_view(), name='user-favorites-detail'),
    
    # User activity
    path('activity/', views.UserActivityView.as_view(), name='user-activity'),
]