# Generated by Django 4.1.7 on 2023-06-22 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0011_alter_paiduser_уровень'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField()),
                ('total_calories', models.IntegerField()),
                ('total_protein', models.IntegerField()),
                ('total_fat', models.IntegerField()),
                ('total_carbs', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram_bot.paiduser')),
            ],
        ),
        migrations.CreateModel(
            name='Meal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_type', models.CharField(choices=[('breakfast', 'Завтрак'), ('lunch', 'Обед'), ('dinner', 'Ужин'), ('snack', 'Перекус')], max_length=10)),
                ('calories', models.IntegerField()),
                ('protein', models.IntegerField()),
                ('fat', models.IntegerField()),
                ('carbs', models.IntegerField()),
                ('course_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram_bot.courseday')),
            ],
        ),
        migrations.DeleteModel(
            name='UserCalories',
        ),
    ]