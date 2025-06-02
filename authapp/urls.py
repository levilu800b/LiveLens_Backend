# type: ignore
# authapp/urls.py


from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView,
    EmailVerificationView, ResendVerificationView,
    UserProfileView, ChangePasswordView, DeleteAccountView,
    UserLibraryListView, UserLibraryCreateView, UserLibraryUpdateView,
    UserFavoritesListView, UserFavoritesCreateView, UserFavoritesDeleteView,
    UserListView, MakeUserAdminView, DeleteUserView, GoogleAuthView
)

app_name = 'authapp'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    
    # User library
    path('library/', UserLibraryListView.as_view(), name='library_list'),
    path('library/add/', UserLibraryCreateView.as_view(), name='library_add'),
    path('library/<int:pk>/update/', UserLibraryUpdateView.as_view(), name='library_update'),
    
    # User favorites
    path('favorites/', UserFavoritesListView.as_view(), name='favorites_list'),
    path('favorites/add/', UserFavoritesCreateView.as_view(), name='favorites_add'),
    path('favorites/remove/', UserFavoritesDeleteView.as_view(), name='favorites_remove'),
    
    # Admin endpoints
    path('admin/users/', UserListView.as_view(), name='admin_users_list'),
    path('admin/make-admin/', MakeUserAdminView.as_view(), name='make_user_admin'),
    path('admin/delete-user/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),
    
    # Google OAuth
    path('google/', GoogleAuthView.as_view(), name='google_auth'),
]