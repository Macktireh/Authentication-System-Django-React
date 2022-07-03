# Generated by Django 3.2.13 on 2022-07-02 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False, help_text='Specifies whether the user should verify their email address.', verbose_name='email verified'),
        ),
    ]
