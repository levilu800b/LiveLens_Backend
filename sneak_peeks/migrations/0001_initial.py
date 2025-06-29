# Generated by Django 5.2.1 on 2025-06-09 12:00

import cloudinary.models
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
            name='SneakPeek',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=220, unique=True)),
                ('description', models.TextField(blank=True)),
                ('short_description', models.TextField(blank=True, help_text='Brief description for previews and social media', max_length=300)),
                ('category', models.CharField(choices=[('upcoming_film', 'Upcoming Film'), ('upcoming_content', 'Upcoming Content'), ('upcoming_story', 'Upcoming Story'), ('upcoming_podcast', 'Upcoming Podcast'), ('upcoming_animation', 'Upcoming Animation'), ('behind_scenes', 'Behind the Scenes'), ('teaser', 'Teaser'), ('trailer', 'Trailer'), ('announcement', 'Announcement'), ('other', 'Other')], default='teaser', max_length=50)),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags (e.g., action, comedy, drama)', max_length=500)),
                ('video_file', cloudinary.models.CloudinaryField(help_text='Main sneak peek video file', max_length=255, verbose_name='video')),
                ('thumbnail', cloudinary.models.CloudinaryField(blank=True, help_text='Thumbnail image for the sneak peek', max_length=255, null=True, verbose_name='image')),
                ('poster', cloudinary.models.CloudinaryField(blank=True, help_text='Poster image for displays', max_length=255, null=True, verbose_name='image')),
                ('duration', models.PositiveIntegerField(default=0, help_text='Duration in seconds')),
                ('video_quality', models.CharField(choices=[('480p', '480p'), ('720p', '720p'), ('1080p', '1080p'), ('4K', '4K')], default='1080p', max_length=10)),
                ('file_size', models.BigIntegerField(default=0, help_text='File size in bytes')),
                ('release_date', models.DateField(blank=True, help_text='Expected release date of the full content', null=True)),
                ('content_rating', models.CharField(choices=[('G', 'General Audiences'), ('PG', 'Parental Guidance'), ('PG-13', 'Parents Strongly Cautioned'), ('R', 'Restricted'), ('NC-17', 'Adults Only')], default='PG', help_text='Content rating', max_length=10)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_trending', models.BooleanField(default=False)),
                ('is_premium', models.BooleanField(default=False, help_text='Requires premium subscription to view')),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('dislike_count', models.PositiveIntegerField(default=0)),
                ('share_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('meta_title', models.CharField(blank=True, max_length=60)),
                ('meta_description', models.CharField(blank=True, max_length=160)),
                ('meta_keywords', models.CharField(blank=True, max_length=255)),
                ('related_content_type', models.CharField(blank=True, help_text='Type of content this sneak peek is for (film, story, etc.)', max_length=50)),
                ('related_content_id', models.UUIDField(blank=True, help_text='ID of the related content if it exists', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sneak_peeks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sneak Peek',
                'verbose_name_plural': 'Sneak Peeks',
                'db_table': 'sneak_peeks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SneakPeekInteraction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('interaction_type', models.CharField(choices=[('like', 'Like'), ('dislike', 'Dislike'), ('share', 'Share'), ('download', 'Download'), ('favorite', 'Favorite'), ('report', 'Report')], max_length=20)),
                ('share_platform', models.CharField(blank=True, help_text='Platform where content was shared', max_length=50)),
                ('rating', models.PositiveIntegerField(blank=True, help_text='Rating from 1-5 stars', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sneak_peek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='sneak_peeks.sneakpeek')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sneak_peek_interactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sneak Peek Interaction',
                'verbose_name_plural': 'Sneak Peek Interactions',
                'db_table': 'sneak_peek_interactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SneakPeekPlaylist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('is_auto_play', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sneak_peek_playlists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sneak Peek Playlist',
                'verbose_name_plural': 'Sneak Peek Playlists',
                'db_table': 'sneak_peek_playlists',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='SneakPeekPlaylistItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sneak_peeks.sneakpeekplaylist')),
                ('sneak_peek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sneak_peeks.sneakpeek')),
            ],
            options={
                'verbose_name': 'Sneak Peek Playlist Item',
                'verbose_name_plural': 'Sneak Peek Playlist Items',
                'db_table': 'sneak_peek_playlist_items',
                'ordering': ['order', 'added_at'],
            },
        ),
        migrations.AddField(
            model_name='sneakpeekplaylist',
            name='sneak_peeks',
            field=models.ManyToManyField(related_name='playlists', through='sneak_peeks.SneakPeekPlaylistItem', to='sneak_peeks.sneakpeek'),
        ),
        migrations.CreateModel(
            name='SneakPeekView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('device_type', models.CharField(choices=[('desktop', 'Desktop'), ('mobile', 'Mobile'), ('tablet', 'Tablet'), ('tv', 'Smart TV'), ('other', 'Other')], default='other', max_length=20)),
                ('watch_duration', models.PositiveIntegerField(default=0, help_text='How long the user watched in seconds')),
                ('completion_percentage', models.FloatField(default=0.0, help_text='Percentage of video watched', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('referrer', models.URLField(blank=True)),
                ('utm_source', models.CharField(blank=True, max_length=100)),
                ('utm_medium', models.CharField(blank=True, max_length=100)),
                ('utm_campaign', models.CharField(blank=True, max_length=100)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('sneak_peek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='sneak_peeks.sneakpeek')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sneak_peek_views', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sneak Peek View',
                'verbose_name_plural': 'Sneak Peek Views',
                'db_table': 'sneak_peek_views',
                'ordering': ['-viewed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sneakpeek',
            index=models.Index(fields=['status', 'is_featured'], name='sneak_peeks_status_605f0b_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeek',
            index=models.Index(fields=['category', 'created_at'], name='sneak_peeks_categor_a40a51_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeek',
            index=models.Index(fields=['author', 'status'], name='sneak_peeks_author__23c015_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeek',
            index=models.Index(fields=['is_trending', 'view_count'], name='sneak_peeks_is_tren_c75d51_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekinteraction',
            index=models.Index(fields=['sneak_peek', 'interaction_type'], name='sneak_peek__sneak_p_018552_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekinteraction',
            index=models.Index(fields=['user', 'interaction_type'], name='sneak_peek__user_id_36d0e8_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sneakpeekinteraction',
            unique_together={('user', 'sneak_peek', 'interaction_type')},
        ),
        migrations.AddIndex(
            model_name='sneakpeekplaylistitem',
            index=models.Index(fields=['playlist', 'order'], name='sneak_peek__playlis_6a6e1b_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sneakpeekplaylistitem',
            unique_together={('playlist', 'sneak_peek')},
        ),
        migrations.AddIndex(
            model_name='sneakpeekplaylist',
            index=models.Index(fields=['creator', 'is_public'], name='sneak_peek__creator_a77d31_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekplaylist',
            index=models.Index(fields=['is_public', 'updated_at'], name='sneak_peek__is_publ_82240f_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekview',
            index=models.Index(fields=['sneak_peek', 'viewed_at'], name='sneak_peek__sneak_p_c8165c_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekview',
            index=models.Index(fields=['user', 'viewed_at'], name='sneak_peek__user_id_036d01_idx'),
        ),
        migrations.AddIndex(
            model_name='sneakpeekview',
            index=models.Index(fields=['ip_address', 'viewed_at'], name='sneak_peek__ip_addr_735d9e_idx'),
        ),
    ]
