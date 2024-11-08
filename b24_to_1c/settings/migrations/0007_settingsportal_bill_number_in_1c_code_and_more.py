# Generated by Django 4.1.1 on 2022-10-06 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0006_settingsportal_document_number_in_1c_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='settingsportal',
            name='bill_number_in_1c_code',
            field=models.CharField(default='UF_CRM_1665054060', help_text='Код поля Номер счета на оплату в 1С в сделке', max_length=30, verbose_name='Код поля Номер счета на оплату в 1С'),
        ),
        migrations.AddField(
            model_name='settingsportal',
            name='invoice_number_in_1c_code',
            field=models.CharField(default='UF_CRM_1665054125', help_text='Код поля Номер счет фактуры в 1С в сделке', max_length=30, verbose_name='Код поля Номер счет фактуры в 1С'),
        ),
        migrations.AddField(
            model_name='settingsportal',
            name='link_print_in_1c_code',
            field=models.CharField(default='UF_CRM_1665054289', help_text='Код поля Ссылка на печатную форму в 1С в сделке', max_length=30, verbose_name='Код поля Ссылка на печатную форму в 1С'),
        ),
        migrations.AddField(
            model_name='settingsportal',
            name='sale_number_in_1c_code',
            field=models.CharField(default='UF_CRM_1665054102', help_text='Код поля Номер расходной накладной в 1С в сделке', max_length=30, verbose_name='Код поля Номер расходной накладной в 1С'),
        ),
    ]
