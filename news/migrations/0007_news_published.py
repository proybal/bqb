# Generated by Django 3.1.5 on 2022-06-05 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0006_auto_20220526_1732'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='published',
            field=models.BooleanField(default=True, verbose_name='Published'),
        ),
    ]
