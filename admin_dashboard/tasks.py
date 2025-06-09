# admin_dashboard/tasks.py
# type: ignore

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_report_async(report_id):
    """Generate report asynchronously"""
    
    try:
        from .models import ReportGeneration
        from .utils import export_analytics_data
        import os
        import uuid
        
        report = ReportGeneration.objects.get(id=report_id)
        report.status = 'processing'
        report.processing_started_at = timezone.now()
        report.save()
        
        # Generate the report based on type
        if report.report_type == 'content_performance':
            data = export_analytics_data(
                report.date_from,
                report.date_to,
                report.filters.get('content_type')
            )
        else:
            # Placeholder for other report types
            data = "Report data not implemented yet"
        
        if data:
            # Save to file
            filename = f"report_{report.id}_{uuid.uuid4().hex[:8]}.{report.report_format}"
            file_path = os.path.join('reports', filename)
            
            # Create reports directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(data)
            
            # Update report
            report.status = 'completed'
            report.file_path = file_path
            report.file_size = os.path.getsize(file_path)
            report.processing_completed_at = timezone.now()
            
            if report.processing_started_at:
                processing_time = (report.processing_completed_at - report.processing_started_at).total_seconds()
                report.processing_time = processing_time
            
            report.save()
            
            logger.info(f"Report {report.id} generated successfully")
        else:
            report.status = 'failed'
            report.error_message = "Failed to generate report data"
            report.save()
            
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {e}")
        try:
            report = ReportGeneration.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = str(e)
            report.save()
        except:
            pass

@shared_task
def update_dashboard_stats():
    """Update dashboard statistics daily"""
    
    try:
        from .utils import calculate_dashboard_stats, cleanup_old_data
        from .models import DashboardStats
        from django.core.cache import cache
        
        # Calculate new stats
        stats_data = calculate_dashboard_stats()
        
        # Save to database
        today = timezone.now().date()
        
        for metric_type, value in stats_data.items():
            if isinstance(value, (int, float)):
                DashboardStats.objects.update_or_create(
                    metric_type=metric_type,
                    stat_type='daily',
                    date=today,
                    defaults={
                        'value': value,
                        'period_start': timezone.now().replace(hour=0, minute=0, second=0),
                        'period_end': timezone.now().replace(hour=23, minute=59, second=59)
                    }
                )
        
        # Clear cache
        cache_key = f"dashboard_overview_{today}"
        cache.delete(cache_key)
        
        # Cleanup old data
        cleanup_old_data()
        
        logger.info("Dashboard stats updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating dashboard stats: {e}")

@shared_task
def generate_content_analytics_daily():
    """Generate content analytics for all content daily"""
    
    try:
        from .utils import generate_content_analytics
        from stories.models import Story
        from media_content.models import Film, Content
        from podcasts.models import Podcast
        from animations.models import Animation
        from sneak_peeks.models import SneakPeek
        
        yesterday = (timezone.now() - timedelta(days=1)).date()
        
        # Generate analytics for each content type
        content_models = [
            ('story', Story),
            ('film', Film),
            ('content', Content),
            ('podcast', Podcast),
            ('animation', Animation),
            ('sneak_peek', SneakPeek),
        ]
        
        total_processed = 0
        
        for content_type_name, model_class in content_models:
            content_items = model_class.objects.filter(status='published')
            
            for item in content_items:
                analytics = generate_content_analytics(
                    content_type_name,
                    item.id,
                    yesterday
                )
                if analytics:
                    total_processed += 1
        
        logger.info(f"Generated analytics for {total_processed} content items")
        
    except Exception as e:
        logger.error(f"Error generating daily content analytics: {e}")

@shared_task
def check_system_health():
    """Check system health and create alerts if needed"""
    
    try:
        from .utils import create_system_alert
        from django.db import connection
        import psutil
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            create_system_alert(
                title="Database Connection Error",
                message=f"Failed to connect to database: {str(e)}",
                alert_type="critical",
                category="system",
                priority=5,
                requires_action=True
            )
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        if usage_percent > 90:
            create_system_alert(
                title="High Disk Usage",
                message=f"Disk usage is at {usage_percent:.1f}%",
                alert_type="critical",
                category="system",
                priority=4,
                requires_action=True
            )
        elif usage_percent > 80:
            create_system_alert(
                title="Disk Usage Warning",
                message=f"Disk usage is at {usage_percent:.1f}%",
                alert_type="warning",
                category="system",
                priority=3
            )
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            create_system_alert(
                title="High Memory Usage",
                message=f"Memory usage is at {memory.percent:.1f}%",
                alert_type="warning",
                category="performance",
                priority=3
            )
        
        logger.info("System health check completed")
        
    except Exception as e:
        logger.error(f"Error during system health check: {e}")
        create_system_alert(
            title="Health Check Failed",
            message=f"System health check failed: {str(e)}",
            alert_type="error",
            category="system",
            priority=3
        )