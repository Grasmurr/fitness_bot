# Generated by Django 4.1.7 on 2023-05-03 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0010_usercalories_day10_requested_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paiduser",
            name="уровень",
            field=models.CharField(
                choices=[("P", "Профессиональный"), ("N", "Новичок")],
                default="N",
                max_length=16,
            ),
        ),
    ]
