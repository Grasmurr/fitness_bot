# Generated by Django 4.1.7 on 2023-04-23 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0005_bankcards'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankcards',
            name='number_of_activations',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
