# Generated by Django 4.1.1 on 2022-09-08 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FieldsActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, verbose_name='Код')),
                ('kind', models.CharField(choices=[('PROPERTIES', 'PROPERTIES'), ('RETURN_PROPERTIES', 'RETURN_PROPERTIES')], default='PROPERTIES', max_length=20, verbose_name='Вид')),
                ('name', models.CharField(max_length=256, verbose_name='Наименование')),
                ('type', models.CharField(choices=[('string', 'Строка'), ('int', 'Целое число'), ('bool', 'Да/Нет'), ('date', 'Дата'), ('datetime', 'Дата/Время'), ('double', 'Число'), ('select', 'Список'), ('text', 'Текст'), ('user', 'Пользователь')], default='string', max_length=10, verbose_name='Тип')),
                ('required', models.BooleanField(default=True, verbose_name='Обязательное')),
                ('multiple', models.BooleanField(default=False, verbose_name='Множественное')),
                ('default', models.CharField(blank=True, max_length=256, null=True, verbose_name='Значение по умолчанию')),
            ],
            options={
                'verbose_name': 'Поле активити',
                'verbose_name_plural': 'Поля активити',
            },
        ),
        migrations.CreateModel(
            name='OptionsForSelect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, verbose_name='Код варианта')),
                ('name', models.CharField(max_length=20, verbose_name='Наименование варианта')),
                ('fields', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='optionsforselect', to='activities.fieldsactivity', verbose_name='Поле списка')),
            ],
            options={
                'verbose_name': 'Вариант для select',
                'verbose_name_plural': 'Варианты для select',
            },
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Наименование')),
                ('code', models.CharField(max_length=50, verbose_name='Код')),
                ('description', models.CharField(max_length=256, verbose_name='Описание')),
                ('handler', models.URLField(verbose_name='URL обработчика')),
                ('auth_user_id', models.IntegerField(default=1, verbose_name='ID пользователя Битрикс24')),
                ('use_subscription', models.BooleanField(default=False, verbose_name='Ожидать ответа')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активность')),
                ('fields', models.ManyToManyField(related_name='activities', to='activities.fieldsactivity', verbose_name='Поля')),
            ],
            options={
                'verbose_name': 'Активити',
                'verbose_name_plural': 'Активити',
            },
        ),
    ]
