# Generated by Django 4.0.6 on 2022-07-27 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockupdater', '0003_tirestock_last_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='tirestock',
            name='available_quantity_by_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
