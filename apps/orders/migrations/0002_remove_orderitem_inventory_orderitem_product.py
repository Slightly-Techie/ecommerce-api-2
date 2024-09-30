# Generated by Django 4.2.2 on 2024-07-03 12:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0008_alter_productcategory_options"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orderitem",
            name="inventory",
        ),
        migrations.AddField(
            model_name="orderitem",
            name="product",
            field=models.ForeignKey(
                default="a152a232-7020-4cf7-a977-6ca62e7f6d4c",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="order_inventory",
                to="products.product",
            ),
            preserve_default=False,
        ),
    ]
