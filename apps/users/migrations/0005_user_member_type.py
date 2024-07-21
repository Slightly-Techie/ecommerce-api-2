# Generated by Django 4.2.2 on 2024-07-21 19:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_otp_secret"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="member_type",
            field=models.CharField(
                choices=[("1", "Techie"), ("2", "Non_Techie")],
                default="2",
                max_length=2,
            ),
        ),
    ]
