# Generated by Django 3.1.7 on 2021-04-02 14:15

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('ebook', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='book',
            name='language',
            field=models.CharField(choices=[('English', 'English'), ('Hindi', 'Hindi'), ('Arabic', 'Arabic'), ('Urdu', 'Urdu')], default='Urdu', max_length=8),
        ),
        migrations.AlterField(
            model_name='sidepanelimages',
            name='position',
            field=models.CharField(choices=[('second_image', 'second_image'), ('yt_video_link', 'yt_video_link'), ('first_image', 'first_image')], max_length=60, unique=True),
        ),
    ]