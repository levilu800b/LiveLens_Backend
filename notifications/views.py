# notifications/views.py - CREATE THIS FILE
# type: ignore

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
import logging

from .models import Notification, NotificationSettings, NotificationTemplate
from .serializers import (
    NotificationSerializer, NotificationSettingsSerializer, 
    NotificationTemplateSerializer
)
from .services import notification_service, create_notification, mark_notification_read
from authapp.permissions import IsAdminUser

logger = logging.getLogger(__name__)

class NotificationListView(generics.ListAPIView):
    """
    List user notifications
    GET /api/notifications/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = int(self.request.query_params.get('limit', 20))
        
        return notification_service.get_user_notifications(
            user=self.request.user,
            limit=limit,
            unread_only=unread_only
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark notification as read
    POST /api/notifications/<id>/read/
    """
    
    success = notification_service.mark_notification_as_read(notification_id, request.user)
    
    if success:
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_clicked(request, notification_id):
    """
    Mark notification as clicked
    POST /api/notifications/<id>/click/
    """
    
    success = notification_service.mark_notification_as_clicked(notification_id, request.user)
    
    if success:
        return Response({
            'success': True,
            'message': 'Notification marked as clicked'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """
    Mark all notifications as read for the user
    POST /api/notifications/mark-all-read/
    """
    
    try:
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Marked {updated_count} notifications as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return Response({
            'error': 'Failed to mark notifications as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """
    Get unread notifications count
    GET /api/notifications/unread-count/
    """
    
    count = notification_service.get_unread_count(request.user)
    
    return Response({
        'unread_count': count
    }, status=status.HTTP_200_OK)

class NotificationSettingsView(APIView):
    """
    Get and update notification settings
    GET/PUT /api/notifications/settings/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        settings_obj, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationSettingsSerializer(settings_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        settings_obj, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationSettingsSerializer(
            settings_obj, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'settings': serializer.data,
                'message': 'Notification settings updated'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid settings data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminBulkNotificationView(APIView):
    """
    Send bulk notifications (admin only)
    POST /api/notifications/send-bulk/
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        try:
            notification_type = request.data.get('notification_type')
            title = request.data.get('title')
            message = request.data.get('message')
            recipient_ids = request.data.get('recipient_ids', [])
            
            if not all([notification_type, title, message]):
                return Response({
                    'error': 'notification_type, title, and message are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get recipients
            from authapp.models import User
            if recipient_ids:
                recipients = User.objects.filter(id__in=recipient_ids)
            else:
                recipients = User.objects.filter(is_active=True)
            
            # Send bulk notification
            notifications = notification_service.send_bulk_notification(
                recipients=list(recipients),
                notification_type=notification_type,
                title=title,
                message=message,
                sender=request.user
            )
            
            return Response({
                'success': True,
                'notifications_sent': len(notifications),
                'total_recipients': recipients.count(),
                'message': 'Bulk notifications sent successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return Response({
                'error': 'Failed to send bulk notifications'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationTemplateListView(generics.ListCreateAPIView):
    """
    List and create notification templates (admin only)
    GET/POST /api/notifications/templates/
    """
    permission_classes = [IsAdminUser]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.filter(is_active=True)