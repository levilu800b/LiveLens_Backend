# email_notifications/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'email_notifications'

urlpatterns = [
    # Newsletter subscription endpoints
    path('newsletter/subscribe/', views.NewsletterSubscriptionView.as_view(), name='newsletter_subscribe'),
    path('newsletter/verify/<str:token>/', views.NewsletterVerificationView.as_view(), name='newsletter_verify'),
    path('newsletter/unsubscribe/<uuid:subscription_id>/', views.NewsletterUnsubscribeView.as_view(), name='newsletter_unsubscribe'),
    path('newsletter/unsubscribe/', views.NewsletterUnsubscribeView.as_view(), name='newsletter_unsubscribe_by_email'),
    
    # User newsletter preferences (authenticated users)
    path('newsletter/preferences/', views.NewsletterPreferencesView.as_view(), name='newsletter_preferences'),
    
    # Admin newsletter management
    path('admin/newsletter/stats/', views.newsletter_stats, name='newsletter_stats'),
    path('admin/newsletter/blast/', views.send_newsletter_blast, name='newsletter_blast'),
]