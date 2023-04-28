# Generated by Django 4.1.7 on 2023-04-16 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_alter_dailycontent_caption_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailycontent',
            name='gif_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='dailycontent',
            name='photo_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='dailycontent',
            name='video_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='specialcontent',
            name='gif_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='specialcontent',
            name='photo_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='specialcontent',
            name='video_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
