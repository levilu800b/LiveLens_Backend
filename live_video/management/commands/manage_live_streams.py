# live_video/management/commands/manage_live_streams.py
# type: ignore

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from live_video.models import LiveVideo, LiveVideoSchedule
from live_video.signals import send_live_video_notification


class Command(BaseCommand):
    help = 'Manage live streams - auto start, auto end, and create scheduled streams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-start',
            action='store_true',
            help='Auto-start scheduled live streams',
        )
        parser.add_argument(
            '--auto-end',
            action='store_true',
            help='Auto-end expired live streams',
        )
        parser.add_argument(
            '--create-scheduled',
            action='store_true',
            help='Create live videos from active schedules',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old ended streams (older than 30 days)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all management tasks',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.auto_start_streams()
            self.auto_end_streams()
            self.create_scheduled_streams()
            self.cleanup_old_streams()
        else:
            if options['auto_start']:
                self.auto_start_streams()
            
            if options['auto_end']:
                self.auto_end_streams()
            
            if options['create_scheduled']:
                self.create_scheduled_streams()
            
            if options['cleanup']:
                self.cleanup_old_streams()

    def auto_start_streams(self):
        """Auto-start live streams that are scheduled to start now"""
        now = timezone.now()
        
        # Find streams scheduled to start within the last 5 minutes
        scheduled_streams = LiveVideo.objects.filter(
            live_status='scheduled',
            auto_start=True,
            scheduled_start_time__lte=now,
            scheduled_start_time__gte=now - timezone.timedelta(minutes=5)
        )
        
        started_count = 0
        for stream in scheduled_streams:
            try:
                stream.start_stream()
                send_live_video_notification(stream, 'started')
                self.stdout.write(
                    self.style.SUCCESS(f'Auto-started live stream: {stream.title}')
                )
                started_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to auto-start stream {stream.title}: {e}')
                )
        
        if started_count == 0:
            self.stdout.write('No streams to auto-start at this time.')
        else:
            self.stdout.write(f'Auto-started {started_count} live streams.')

    def auto_end_streams(self):
        """Auto-end live streams that have exceeded their scheduled duration"""
        now = timezone.now()
        
        # Find live streams that should have ended
        expired_streams = LiveVideo.objects.filter(
            live_status='live',
            scheduled_end_time__isnull=False,
            scheduled_end_time__lte=now
        )
        
        ended_count = 0
        for stream in expired_streams:
            try:
                stream.end_stream()
                self.stdout.write(
                    self.style.SUCCESS(f'Auto-ended expired live stream: {stream.title}')
                )
                ended_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to auto-end stream {stream.title}: {e}')
                )
        
        if ended_count == 0:
            self.stdout.write('No streams to auto-end at this time.')
        else:
            self.stdout.write(f'Auto-ended {ended_count} live streams.')

    def create_scheduled_streams(self):
        """Create live videos from active schedules"""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        active_schedules = LiveVideoSchedule.objects.filter(is_active=True)
        
        created_count = 0
        for schedule in active_schedules:
            try:
                # Check if we need to create a live video for this schedule
                next_scheduled_time = self.get_next_scheduled_time(schedule, now)
                
                if next_scheduled_time:
                    # Check if a live video already exists for this time slot
                    existing = LiveVideo.objects.filter(
                        author=schedule.author,
                        scheduled_start_time__date=next_scheduled_time.date(),
                        scheduled_start_time__time=schedule.start_time
                    ).exists()
                    
                    if not existing:
                        live_video = schedule.create_next_live_video()
                        if live_video:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created live video from schedule: {live_video.title}'
                                )
                            )
                            created_count += 1
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create live video from schedule {schedule.title_template}: {e}')
                )
        
        if created_count == 0:
            self.stdout.write('No new live videos created from schedules.')
        else:
            self.stdout.write(f'Created {created_count} live videos from schedules.')

    def cleanup_old_streams(self):
        """Clean up old ended streams"""
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        old_streams = LiveVideo.objects.filter(
            live_status='ended',
            actual_end_time__lt=cutoff_date
        )
        
        count = old_streams.count()
        if count > 0:
            # You might want to archive these instead of deleting
            # For now, we'll just report them
            self.stdout.write(
                self.style.WARNING(f'Found {count} old streams that could be archived/cleaned up')
            )
            
            # Uncomment the line below if you want to actually delete them
            # old_streams.delete()
            # self.stdout.write(f'Deleted {count} old live streams.')
        else:
            self.stdout.write('No old streams to clean up.')

    def get_next_scheduled_time(self, schedule, now):
        """Calculate the next scheduled time for a schedule"""
        from datetime import datetime, timedelta
        
        if schedule.frequency == 'daily':
            # Create for tomorrow if today's stream hasn't been created
            tomorrow = now.date() + timedelta(days=1)
            return timezone.make_aware(datetime.combine(tomorrow, schedule.start_time))
        
        elif schedule.frequency == 'weekly' and schedule.weekday is not None:
            # Calculate next weekly occurrence
            days_ahead = schedule.weekday - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_date = now.date() + timedelta(days=days_ahead)
            return timezone.make_aware(datetime.combine(next_date, schedule.start_time))
        
        elif schedule.frequency == 'monthly' and schedule.day_of_month is not None:
            # Calculate next monthly occurrence
            if now.day < schedule.day_of_month:
                next_date = now.date().replace(day=schedule.day_of_month)
            else:
                # Next month
                if now.month == 12:
                    next_date = now.date().replace(year=now.year + 1, month=1, day=schedule.day_of_month)
                else:
                    next_date = now.date().replace(month=now.month + 1, day=schedule.day_of_month)
            
            return timezone.make_aware(datetime.combine(next_date, schedule.start_time))
        
        return None