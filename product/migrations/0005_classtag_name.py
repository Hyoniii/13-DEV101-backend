# Generated by Django 3.1.3 on 2020-11-05 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20201104_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='classtag',
            name='name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]