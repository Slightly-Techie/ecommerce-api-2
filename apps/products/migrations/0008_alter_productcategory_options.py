# Generated by Django 4.2.2 on 2024-05-30 22:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_rename_products_product'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productcategory',
            options={'ordering': ('created_at',), 'verbose_name_plural': 'product categories'},
        ),
    ]
