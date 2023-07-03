# Generated by Django 4.1.7 on 2023-06-22 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0012_courseday_meal_delete_usercalories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseday',
            name='total_calories',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='courseday',
            name='total_carbs',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='courseday',
            name='total_fat',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='courseday',
            name='total_protein',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='meal',
            name='calories',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='meal',
            name='carbs',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='meal',
            name='fat',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='meal',
            name='protein',
            field=models.IntegerField(default=0),
        ),
    ]