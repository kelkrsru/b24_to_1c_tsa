# Generated by Django 4.1.1 on 2022-10-06 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0005_settingsportal_airline_code_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='settingsportal',
            name='document_number_in_1c_code',
            field=models.CharField(default='UF_CRM_1665034515', help_text='Код поля Номер заявки в 1С в сделке', max_length=30, verbose_name='Код поля Номер заявки в 1С'),
        ),
        migrations.AddField(
            model_name='settingsportal',
            name='my_company_inn',
            field=models.CharField(default='2465253470', help_text='ИНН моей компании для передачи в 1С', max_length=20, verbose_name='ИНН моей компании'),
        ),
    ]
