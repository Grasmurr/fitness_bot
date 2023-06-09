# Generated by Django 4.1.7 on 2023-04-23 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0004_alter_paiduser_место_alter_paiduser_пол_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="BankCards",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bank_name", models.CharField(blank=True, max_length=15, null=True)),
                ("card_number", models.CharField(blank=True, max_length=25, null=True)),
                ("number_of_activations", models.IntegerField(blank=True, null=True)),
            ],
        ),
    ]
