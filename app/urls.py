# type: ignore

# app/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authapp.urls')),
    path('api/stories/', include('stories.urls')),
    path('api/media/', include('media_content.urls')),
    path('api/podcasts/', include('podcasts.urls')),
    path('api/animations/', include('animations.urls')),
    path('api/sneak-peeks/', include('sneak_peeks.urls')),
    path('api/comments/', include('comments.urls')),
    path('api/admin-dashboard/', include('admin_dashboard.urls')),
    path('api/password-reset/', include('password_reset.urls')),
    path('api/ai/', include('ai_services.urls')),
    path('tinymce/', include('tinymce.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)