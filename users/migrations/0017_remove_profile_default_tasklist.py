# Generated by Django 3.0.3 on 2020-05-07 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_profile_default_tasklist'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='default_tasklist',
        ),
    ]
