# admin_dashboard/views.py
# type: ignore

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Sum, Avg
from django.core.cache import cache
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import (
    DashboardStats, ContentAnalytics, UserActivity,
    SystemAlert, ReportGeneration
)
from .serializers import (
    DashboardOverviewSerializer, ContentAnalyticsSerializer,
    UserActivitySerializer, SystemAlertSerializer,
    ReportGenerationSerializer
)
from .utils import calculate_dashboard_stats, generate_analytics_report

User = get_user_model()


def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def dashboard_overview(request):
    """Get dashboard overview statistics"""
    try:
        # Try to get cached data first
        cache_key = 'dashboard_overview_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            serializer = DashboardOverviewSerializer(cached_data)
            return Response(serializer.data)
        
        # Calculate fresh stats
        stats = calculate_dashboard_stats()
        
        # Cache the results for 5 minutes
        cache.set(cache_key, stats, 300)
        
        serializer = DashboardOverviewSerializer(stats)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard overview: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def analytics_summary(request):
    """Get analytics summary"""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Calculate analytics
        analytics = {
            'total_users': User.objects.count(),
            'new_users': User.objects.filter(
                date_joined__gte=start_date
            ).count(),
            'active_users': User.objects.filter(
                last_login__gte=start_date
            ).count(),
            'content_stats': {
                'total_stories': 0,  # You can implement this based on your models
                'total_podcasts': 0,
                'total_animations': 0,
            }
        }
        
        return Response(analytics)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get analytics summary: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def user_management_stats(request):
    """Get user management statistics"""
    try:
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get user stats: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ContentAnalyticsListView(generics.ListAPIView):
    """List content analytics"""
    serializer_class = ContentAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return ContentAnalytics.objects.all().order_by('-created_at')


class UserActivityListView(generics.ListAPIView):
    """List user activities"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return UserActivity.objects.all().order_by('-timestamp')


class SystemAlertListCreateView(generics.ListCreateAPIView):
    """List and create system alerts"""
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return SystemAlert.objects.all().order_by('-created_at')


class SystemAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detail view for system alerts"""
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return SystemAlert.objects.all()


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_alerts_as_read(request):
    """Mark alerts as read"""
    try:
        alert_ids = request.data.get('alert_ids', [])
        
        if alert_ids:
            SystemAlert.objects.filter(
                id__in=alert_ids
            ).update(is_read=True)
        else:
            # Mark all as read
            SystemAlert.objects.filter(
                is_read=False
            ).update(is_read=True)
        
        return Response({'message': 'Alerts marked as read'})
        
    except Exception as e:
        return Response(
            {'error': f'Failed to mark alerts as read: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def resolve_alert(request, alert_id):
    """Resolve a specific alert"""
    try:
        alert = get_object_or_404(SystemAlert, id=alert_id)
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        
        return Response({'message': 'Alert resolved successfully'})
        
    except SystemAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to resolve alert: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ReportGenerationListCreateView(generics.ListCreateAPIView):
    """List and create reports"""
    serializer_class = ReportGenerationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return ReportGeneration.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def download_report(request, report_id):
    """Download a generated report"""
    try:
        report = get_object_or_404(ReportGeneration, id=report_id)
        
        if not report.file_path:
            return Response(
                {'error': 'Report file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return file download response
        response = HttpResponse(content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{report.name}.csv"'
        
        # You would implement actual file reading here
        response.write('Report data would go here')
        
        return response
        
    except ReportGeneration.DoesNotExist:
        return Response(
            {'error': 'Report not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to download report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

