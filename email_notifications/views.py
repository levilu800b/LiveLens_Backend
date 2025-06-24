# email_notifications/views.py
# type: ignore

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import NewsletterSubscription, EmailNotification
from .serializers import NewsletterSubscriptionSerializer
from .utils import send_newsletter_confirmation_email, generate_newsletter_token
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class NewsletterSubscriptionView(APIView):
    """
    Handle newsletter subscription from footer and elsewhere
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Subscribe to newsletter"""
        try:
            email = request.data.get('email', '').strip().lower()
            source = request.data.get('source', 'footer')
            
            if not email:
                return Response({
                    'error': 'Email address is required.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                return Response({
                    'error': 'Please enter a valid email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already subscribed
            existing_subscription = NewsletterSubscription.objects.filter(
                email=email
            ).first()
            
            if existing_subscription:
                if existing_subscription.is_active and existing_subscription.is_verified:
                    return Response({
                        'message': 'You are already subscribed to our newsletter!'
                    }, status=status.HTTP_200_OK)
                elif existing_subscription.is_active and not existing_subscription.is_verified:
                    # Resend verification email
                    verification_token = generate_newsletter_token(email)
                    existing_subscription.verification_token = verification_token
                    existing_subscription.save()
                    
                    send_newsletter_confirmation_email(email, verification_token)
                    
                    return Response({
                        'message': 'Verification email resent! Please check your inbox.',
                        'subscription_id': str(existing_subscription.id)
                    }, status=status.HTTP_200_OK)
                else:
                    # Reactivate subscription
                    existing_subscription.is_active = True
                    existing_subscription.subscribed_at = timezone.now()
                    existing_subscription.unsubscribed_at = None
                    verification_token = generate_newsletter_token(email)
                    existing_subscription.verification_token = verification_token
                    existing_subscription.save()
                    
                    send_newsletter_confirmation_email(email, verification_token)
                    
                    return Response({
                        'message': 'Please check your email to confirm your subscription.',
                        'subscription_id': str(existing_subscription.id)
                    }, status=status.HTTP_201_CREATED)
            
            # Check if user exists
            user = None
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
            
            # Create new subscription
            verification_token = generate_newsletter_token(email)
            
            subscription = NewsletterSubscription.objects.create(
                email=email,
                user=user,
                verification_token=verification_token,
                subscription_source=source,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send confirmation email
            send_newsletter_confirmation_email(email, verification_token)
            
            return Response({
                'message': 'Thank you for subscribing! Please check your email to confirm your subscription.',
                'subscription_id': str(subscription.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Newsletter subscription error: {str(e)}")
            return Response({
                'error': 'Something went wrong. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class NewsletterVerificationView(APIView):
    """
    Handle newsletter subscription verification
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """Verify newsletter subscription"""
        try:
            subscription = get_object_or_404(
                NewsletterSubscription,
                verification_token=token,
                is_active=True
            )
            
            if subscription.is_verified:
                return Response({
                    'message': 'Your subscription is already verified!'
                }, status=status.HTTP_200_OK)
            
            # Verify subscription
            subscription.verify_subscription()
            
            return Response({
                'message': 'Your newsletter subscription has been confirmed! Welcome to LiveLens updates.',
                'subscription_id': str(subscription.id)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Newsletter verification error: {str(e)}")
            return Response({
                'error': 'Invalid or expired verification link.'
            }, status=status.HTTP_400_BAD_REQUEST)

class NewsletterUnsubscribeView(APIView):
    """
    Handle newsletter unsubscription
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, subscription_id):
        """Unsubscribe from newsletter"""
        try:
            subscription = get_object_or_404(
                NewsletterSubscription,
                id=subscription_id,
                is_active=True
            )
            
            subscription.unsubscribe()
            
            return Response({
                'message': 'You have been successfully unsubscribed from our newsletter.',
                'email': subscription.email
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Newsletter unsubscribe error: {str(e)}")
            return Response({
                'error': 'Invalid unsubscribe link.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """Unsubscribe by email"""
        try:
            email = request.data.get('email', '').strip().lower()
            
            if not email:
                return Response({
                    'error': 'Email address is required.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subscription = NewsletterSubscription.objects.filter(
                email=email,
                is_active=True
            ).first()
            
            if subscription:
                subscription.unsubscribe()
                return Response({
                    'message': 'You have been successfully unsubscribed from our newsletter.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Email address not found in our subscription list.'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Newsletter unsubscribe by email error: {str(e)}")
            return Response({
                'error': 'Something went wrong. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NewsletterPreferencesView(APIView):
    """
    Handle newsletter subscription preferences for authenticated users
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's newsletter preferences"""
        try:
            subscription = NewsletterSubscription.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if subscription:
                serializer = NewsletterSubscriptionSerializer(subscription)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'subscribed': False,
                    'message': 'User is not subscribed to newsletter.'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Newsletter preferences get error: {str(e)}")
            return Response({
                'error': 'Something went wrong. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Update user's newsletter preferences"""
        try:
            subscription, created = NewsletterSubscription.objects.get_or_create(
                user=request.user,
                defaults={
                    'email': request.user.email,
                    'is_verified': True,  # User is already verified
                    'subscription_source': 'profile_settings'
                }
            )
            
            # Update preferences
            subscription.content_uploads = request.data.get('content_uploads', subscription.content_uploads)
            subscription.live_videos = request.data.get('live_videos', subscription.live_videos)
            subscription.weekly_digest = request.data.get('weekly_digest', subscription.weekly_digest)
            subscription.monthly_newsletter = request.data.get('monthly_newsletter', subscription.monthly_newsletter)
            subscription.is_active = request.data.get('subscribed', subscription.is_active)
            
            subscription.save()
            
            serializer = NewsletterSubscriptionSerializer(subscription)
            return Response({
                'message': 'Newsletter preferences updated successfully.',
                'subscription': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Newsletter preferences update error: {str(e)}")
            return Response({
                'error': 'Something went wrong. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def newsletter_stats(request):
    """
    Get newsletter subscription statistics (Admin only)
    """
    try:
        total_subscriptions = NewsletterSubscription.objects.count()
        active_subscriptions = NewsletterSubscription.objects.filter(is_active=True).count()
        verified_subscriptions = NewsletterSubscription.objects.filter(
            is_active=True, 
            is_verified=True
        ).count()
        
        # Recent subscriptions (last 30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_subscriptions = NewsletterSubscription.objects.filter(
            subscribed_at__gte=thirty_days_ago
        ).count()
        
        # Subscription sources breakdown
        sources = NewsletterSubscription.objects.filter(
            is_active=True
        ).values('subscription_source').annotate(
            count=models.Count('id')
        )
        
        # Email notification stats
        total_emails_sent = EmailNotification.objects.filter(status='sent').count()
        failed_emails = EmailNotification.objects.filter(status='failed').count()
        
        return Response({
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'verified_subscriptions': verified_subscriptions,
            'recent_subscriptions': recent_subscriptions,
            'subscription_sources': list(sources),
            'email_stats': {
                'total_sent': total_emails_sent,
                'failed': failed_emails,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Newsletter stats error: {str(e)}")
        return Response({
            'error': 'Failed to fetch newsletter statistics.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def send_newsletter_blast(request):
    """
    Send newsletter to all subscribers (Admin only)
    """
    try:
        subject = request.data.get('subject')
        content = request.data.get('content')
        newsletter_type = request.data.get('type', 'custom')
        
        if not subject or not content:
            return Response({
                'error': 'Subject and content are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get active subscribers
        subscribers = NewsletterSubscription.objects.filter(
            is_active=True,
            is_verified=True
        )
        
        if newsletter_type == 'weekly_digest':
            subscribers = subscribers.filter(weekly_digest=True)
        elif newsletter_type == 'monthly_newsletter':
            subscribers = subscribers.filter(monthly_newsletter=True)
        
        # This would be handled by a background task in production
        # For now, we'll just create the notification records
        notifications_created = 0
        for subscriber in subscribers:
            EmailNotification.objects.create(
                recipient_email=subscriber.email,
                recipient_user=subscriber.user,
                notification_type=newsletter_type,
                subject=subject,
                status='pending'
            )
            notifications_created += 1
        
        return Response({
            'message': f'Newsletter queued for {notifications_created} subscribers.',
            'subscribers_count': notifications_created
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Newsletter blast error: {str(e)}")
        return Response({
            'error': 'Failed to send newsletter.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)