# Generated by Django 4.2.2 on 2024-05-30 12:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="inventory",
            options={"verbose_name_plural": "inventories"},
        ),
    ]
