# Generated by Django 5.2.1 on 2025-06-03 17:23

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True)),
                ('description', models.TextField(help_text='Detailed description of the content', max_length=1000)),
                ('short_description', models.CharField(blank=True, help_text='Brief description for cards', max_length=300)),
                ('category', models.CharField(choices=[('action', 'Action'), ('adventure', 'Adventure'), ('comedy', 'Comedy'), ('drama', 'Drama'), ('horror', 'Horror'), ('romance', 'Romance'), ('sci_fi', 'Science Fiction'), ('fantasy', 'Fantasy'), ('thriller', 'Thriller'), ('documentary', 'Documentary'), ('animation', 'Animation'), ('mystery', 'Mystery'), ('crime', 'Crime'), ('biography', 'Biography'), ('history', 'History'), ('music', 'Music'), ('sport', 'Sport'), ('family', 'Family'), ('educational', 'Educational'), ('tech', 'Technology'), ('lifestyle', 'Lifestyle'), ('other', 'Other')], default='other', max_length=20)),
                ('tags', models.JSONField(blank=True, default=list, help_text='List of tags for the content')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='media/thumbnails/')),
                ('poster', models.ImageField(blank=True, null=True, upload_to='media/posters/')),
                ('banner', models.ImageField(blank=True, help_text='Large banner image', null=True, upload_to='media/banners/')),
                ('video_file', models.FileField(blank=True, help_text='Main video file', null=True, upload_to='media/videos/')),
                ('trailer_file', models.FileField(blank=True, help_text='Trailer video file', null=True, upload_to='media/trailers/')),
                ('duration', models.PositiveIntegerField(default=0, help_text='Duration in seconds', validators=[django.core.validators.MinValueValidator(0)])),
                ('trailer_duration', models.PositiveIntegerField(default=0, help_text='Trailer duration in seconds', validators=[django.core.validators.MinValueValidator(0)])),
                ('video_quality', models.CharField(choices=[('360p', '360p'), ('480p', '480p'), ('720p', '720p HD'), ('1080p', '1080p Full HD'), ('1440p', '1440p QHD'), ('2160p', '4K UHD')], default='1080p', max_length=10)),
                ('file_size', models.BigIntegerField(default=0, help_text='File size in bytes')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived'), ('processing', 'Processing')], default='draft', max_length=12)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_trending', models.BooleanField(default=False)),
                ('is_premium', models.BooleanField(default=False, help_text='Requires premium subscription')),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('average_rating', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)])),
                ('rating_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('release_year', models.PositiveIntegerField(blank=True, null=True)),
                ('language', models.CharField(default='English', max_length=50)),
                ('subtitles_available', models.JSONField(blank=True, default=list, help_text='List of available subtitle languages')),
                ('content_type', models.CharField(choices=[('tutorial', 'Tutorial'), ('review', 'Review'), ('vlog', 'Vlog'), ('interview', 'Interview'), ('presentation', 'Presentation'), ('webinar', 'Webinar'), ('course', 'Course'), ('entertainment', 'Entertainment'), ('news', 'News'), ('sports', 'Sports'), ('music_video', 'Music Video'), ('trailer', 'Trailer'), ('commercial', 'Commercial'), ('short_film', 'Short Film'), ('documentary', 'Documentary'), ('other', 'Other')], default='other', max_length=20)),
                ('creator', models.CharField(blank=True, help_text='Content creator/host', max_length=200)),
                ('series_name', models.CharField(blank=True, help_text='Series or channel name', max_length=200)),
                ('episode_number', models.PositiveIntegerField(blank=True, null=True)),
                ('difficulty_level', models.CharField(blank=True, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'), ('expert', 'Expert')], max_length=20)),
                ('is_live', models.BooleanField(default=False)),
                ('scheduled_live_time', models.DateTimeField(blank=True, null=True)),
                ('live_stream_url', models.URLField(blank=True, help_text='Live stream URL')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_authored', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Content',
                'verbose_name_plural': 'Content',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True)),
                ('description', models.TextField(help_text='Detailed description of the content', max_length=1000)),
                ('short_description', models.CharField(blank=True, help_text='Brief description for cards', max_length=300)),
                ('category', models.CharField(choices=[('action', 'Action'), ('adventure', 'Adventure'), ('comedy', 'Comedy'), ('drama', 'Drama'), ('horror', 'Horror'), ('romance', 'Romance'), ('sci_fi', 'Science Fiction'), ('fantasy', 'Fantasy'), ('thriller', 'Thriller'), ('documentary', 'Documentary'), ('animation', 'Animation'), ('mystery', 'Mystery'), ('crime', 'Crime'), ('biography', 'Biography'), ('history', 'History'), ('music', 'Music'), ('sport', 'Sport'), ('family', 'Family'), ('educational', 'Educational'), ('tech', 'Technology'), ('lifestyle', 'Lifestyle'), ('other', 'Other')], default='other', max_length=20)),
                ('tags', models.JSONField(blank=True, default=list, help_text='List of tags for the content')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='media/thumbnails/')),
                ('poster', models.ImageField(blank=True, null=True, upload_to='media/posters/')),
                ('banner', models.ImageField(blank=True, help_text='Large banner image', null=True, upload_to='media/banners/')),
                ('video_file', models.FileField(blank=True, help_text='Main video file', null=True, upload_to='media/videos/')),
                ('trailer_file', models.FileField(blank=True, help_text='Trailer video file', null=True, upload_to='media/trailers/')),
                ('duration', models.PositiveIntegerField(default=0, help_text='Duration in seconds', validators=[django.core.validators.MinValueValidator(0)])),
                ('trailer_duration', models.PositiveIntegerField(default=0, help_text='Trailer duration in seconds', validators=[django.core.validators.MinValueValidator(0)])),
                ('video_quality', models.CharField(choices=[('360p', '360p'), ('480p', '480p'), ('720p', '720p HD'), ('1080p', '1080p Full HD'), ('1440p', '1440p QHD'), ('2160p', '4K UHD')], default='1080p', max_length=10)),
                ('file_size', models.BigIntegerField(default=0, help_text='File size in bytes')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived'), ('processing', 'Processing')], default='draft', max_length=12)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_trending', models.BooleanField(default=False)),
                ('is_premium', models.BooleanField(default=False, help_text='Requires premium subscription')),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('average_rating', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)])),
                ('rating_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('release_year', models.PositiveIntegerField(blank=True, null=True)),
                ('language', models.CharField(default='English', max_length=50)),
                ('subtitles_available', models.JSONField(blank=True, default=list, help_text='List of available subtitle languages')),
                ('director', models.CharField(blank=True, help_text='Film director(s)', max_length=200)),
                ('cast', models.JSONField(blank=True, default=list, help_text='List of main cast members')),
                ('producer', models.CharField(blank=True, help_text='Film producer(s)', max_length=200)),
                ('studio', models.CharField(blank=True, help_text='Production studio', max_length=100)),
                ('budget', models.DecimalField(blank=True, decimal_places=2, help_text='Production budget', max_digits=15, null=True)),
                ('box_office', models.DecimalField(blank=True, decimal_places=2, help_text='Box office earnings', max_digits=15, null=True)),
                ('mpaa_rating', models.CharField(choices=[('G', 'G - General Audiences'), ('PG', 'PG - Parental Guidance'), ('PG-13', 'PG-13 - Parents Strongly Cautioned'), ('R', 'R - Restricted'), ('NC-17', 'NC-17 - Adults Only'), ('NR', 'Not Rated')], default='NR', max_length=10)),
                ('is_series', models.BooleanField(default=False)),
                ('series_name', models.CharField(blank=True, max_length=200)),
                ('episode_number', models.PositiveIntegerField(blank=True, null=True)),
                ('season_number', models.PositiveIntegerField(blank=True, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_authored', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Film',
                'verbose_name_plural': 'Films',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=True)),
                ('is_auto_play', models.BooleanField(default=True, help_text='Auto-play next item in playlist')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='playlists/thumbnails/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Playlist',
                'verbose_name_plural': 'Playlists',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MediaCollection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.ManyToManyField(blank=True, related_name='collections', to='media_content.content')),
                ('films', models.ManyToManyField(blank=True, related_name='collections', to='media_content.film')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_collections', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Media Collection',
                'verbose_name_plural': 'Media Collections',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.CreateModel(
            name='MediaInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('film', 'Film'), ('content', 'Content')], max_length=20)),
                ('object_id', models.UUIDField()),
                ('interaction_type', models.CharField(choices=[('like', 'Like'), ('watch', 'Watch'), ('bookmark', 'Bookmark'), ('share', 'Share'), ('download', 'Download'), ('rate', 'Rate')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('watch_progress', models.FloatField(default=0.0, help_text='Percentage watched (0-100)')),
                ('watch_time', models.PositiveIntegerField(default=0, help_text='Time watched in seconds')),
                ('rating', models.PositiveIntegerField(blank=True, help_text='Rating from 1-5 stars', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Media Interaction',
                'verbose_name_plural': 'Media Interactions',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['content_type', 'object_id'], name='media_conte_content_21059c_idx'), models.Index(fields=['user', 'interaction_type'], name='media_conte_user_id_463936_idx')],
                'unique_together': {('user', 'content_type', 'object_id', 'interaction_type')},
            },
        ),
        migrations.CreateModel(
            name='MediaView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('film', 'Film'), ('content', 'Content')], max_length=20)),
                ('object_id', models.UUIDField()),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('watch_duration', models.PositiveIntegerField(default=0, help_text='Time watched in seconds')),
                ('completion_percentage', models.FloatField(default=0.0, help_text='Percentage of content watched')),
                ('quality_watched', models.CharField(blank=True, choices=[('360p', '360p'), ('480p', '480p'), ('720p', '720p HD'), ('1080p', '1080p Full HD'), ('1440p', '1440p QHD'), ('2160p', '4K UHD')], max_length=10)),
                ('device_type', models.CharField(choices=[('desktop', 'Desktop'), ('mobile', 'Mobile'), ('tablet', 'Tablet'), ('tv', 'Smart TV'), ('other', 'Other')], default='other', max_length=20)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Media View',
                'verbose_name_plural': 'Media Views',
                'ordering': ['-viewed_at'],
                'indexes': [models.Index(fields=['content_type', 'object_id'], name='media_conte_content_125341_idx'), models.Index(fields=['viewed_at'], name='media_conte_viewed__156ba0_idx')],
            },
        ),
        migrations.CreateModel(
            name='PlaylistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('film', 'Film'), ('content', 'Content')], max_length=20)),
                ('object_id', models.UUIDField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='media_content.playlist')),
            ],
            options={
                'verbose_name': 'Playlist Item',
                'verbose_name_plural': 'Playlist Items',
                'ordering': ['playlist', 'order'],
                'unique_together': {('playlist', 'content_type', 'object_id')},
            },
        ),
    ]
