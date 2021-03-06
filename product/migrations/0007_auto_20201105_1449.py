# Generated by Django 3.1.3 on 2020-11-05 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_auto_20201105_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='is_checked',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_open',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='review',
            name='good_bad',
            field=models.BooleanField(null=True),
        ),
    ]
