# Generated by Django 4.1.7 on 2023-06-26 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0014_finisheduser_proteins'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiduser',
            name='proteins',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
