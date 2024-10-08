# Generated by Django 4.2.2 on 2024-09-19 13:19

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reviews', '0003_appreview'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productreview',
            options={'ordering': ('created_at',)},
        ),
        migrations.AlterUniqueTogether(
            name='appreview',
            unique_together={('user',)},
        ),
    ]
