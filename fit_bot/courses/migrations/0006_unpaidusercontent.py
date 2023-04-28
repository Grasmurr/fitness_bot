# Generated by Django 4.1.7 on 2023-04-23 14:43

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0007_paiduser_full_name'),
        ('courses', '0005_dailycontent_gif_file_id_dailycontent_photo_file_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnpaidUserContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(null=True)),
                ('content_type', models.CharField(choices=[('V', 'Video'), ('T', 'Text'), ('P', 'Photo'), ('G', 'GIF')], default='T', max_length=1)),
                ('video', models.FileField(blank=True, null=True, upload_to='videos/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['mp4'])])),
                ('photo', models.ImageField(blank=True, null=True, upload_to='photos/')),
                ('gif', models.FileField(blank=True, null=True, upload_to='gifs/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['gif'])])),
                ('video_file_id', models.CharField(blank=True, max_length=100, null=True)),
                ('photo_file_id', models.CharField(blank=True, max_length=100, null=True)),
                ('gif_file_id', models.CharField(blank=True, max_length=100, null=True)),
                ('caption', models.TextField(blank=True, null=True)),
                ('sequence_number', models.PositiveIntegerField(null=True)),
                ('unpaid_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unpaid_user_contents', to='telegram_bot.unpaiduser')),
            ],
            options={
                'ordering': ['sequence_number'],
            },
        ),
    ]
