# authapp/migrations/0006_create_missing_useractivity.py
# This migration creates the UserActivity table that should have been created in 0002

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('authapp', '0005_revert_avatar_to_imagefield'),
    ]

    operations = [
        # Check if table exists before creating it
        migrations.RunSQL(
            # Forward SQL - Create table if it doesn't exist
            sql="""
            CREATE TABLE IF NOT EXISTS authapp_useractivity (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                activity_type VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                ip_address CHAR(39) NULL,
                user_agent TEXT NOT NULL,
                timestamp DATETIME(6) NOT NULL,
                extra_data JSON NOT NULL,
                user_id BIGINT NOT NULL,
                CONSTRAINT authapp_useractivity_user_id_fk 
                    FOREIGN KEY (user_id) REFERENCES authapp_user (id) 
                    ON DELETE CASCADE,
                INDEX authapp_useractivity_user_id_idx (user_id)
            );
            """,
            
            # Reverse SQL - Drop table
            reverse_sql="DROP TABLE IF EXISTS authapp_useractivity;"
        ),
    ]