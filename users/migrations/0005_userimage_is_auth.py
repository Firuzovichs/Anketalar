# Generated by Django 5.2.1 on 2025-06-11 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_userprofileextension'),
    ]

    operations = [
        migrations.AddField(
            model_name='userimage',
            name='is_auth',
            field=models.BooleanField(default=False),
        ),
    ]
