# type: ignore

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/auth/', include('authapp.urls')),
    path('api/password-reset/', include('password_reset.urls')),
    path('api/comments/', include('comments.urls')),
    path('api/stories/', include('stories.urls')),
    path('api/media/', include('media_content.urls')),
    path('api/podcasts/', include('podcasts.urls')),
    path('api/animations/', include('animations.urls')),
    path('api/sneak-peeks/', include('sneak_peeks.urls')),
    path('api/admin-dashboard/', include('admin_dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar in development
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass