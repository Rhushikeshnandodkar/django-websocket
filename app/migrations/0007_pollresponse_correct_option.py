# Generated by Django 5.1.4 on 2025-01-10 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_pollresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='pollresponse',
            name='correct_option',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
