# Generated by Django 3.1.3 on 2020-11-05 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_auto_20201105_1449'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClassTag',
            new_name='SummaryTag',
        ),
        migrations.RenameField(
            model_name='introduction',
            old_name='process_url',
            new_name='process_image_url',
        ),
        migrations.RenameField(
            model_name='introduction',
            old_name='theme_url',
            new_name='theme_image_url',
        ),
        migrations.RenameField(
            model_name='introduction',
            old_name='work_url',
            new_name='work_image_url',
        ),
        migrations.RenameField(
            model_name='titlecover',
            old_name='cover_url',
            new_name='cover_image_url',
        ),
        migrations.RenameField(
            model_name='titlecover',
            old_name='thumbnail_url',
            new_name='thumbnail_image_url',
        ),
        migrations.RemoveField(
            model_name='summary',
            name='image',
        ),
        migrations.AddField(
            model_name='summary',
            name='image_url',
            field=models.URLField(default='https://images.unsplash.com/photo-1592959755315-6da7782551a9?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80', max_length=2000),
            preserve_default=False,
        ),
        migrations.AlterModelTable(
            name='summarytag',
            table='summary_tags',
        ),
    ]
