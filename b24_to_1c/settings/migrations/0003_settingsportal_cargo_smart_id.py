# Generated by Django 4.1.1 on 2022-10-04 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0002_remove_settingsportal_id_smart_process_cargo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='settingsportal',
            name='cargo_smart_id',
            field=models.PositiveSmallIntegerField(default=0, help_text='ID smart процесса, в котором ведется учет грузов', verbose_name='ID smart процесса Груз'),
        ),
    ]
