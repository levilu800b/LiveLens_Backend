# type: ignore

# app/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication APIs
    path('api/auth/', include('authapp.urls')),
    path('api/password-reset/', include('password_reset.urls')),
    
    # Content APIs (will be added in next steps)
    # path('api/stories/', include('stories.urls')),
    # path('api/media/', include('media_content.urls')),
    # path('api/podcasts/', include('podcasts.urls')),
    # path('api/animations/', include('animations.urls')),
    # path('api/sneak-peeks/', include('sneak_peeks.urls')),
    # path('api/comments/', include('comments.urls')),
    # path('api/admin-dashboard/', include('admin_dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)