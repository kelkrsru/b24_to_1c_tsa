from core.models import Portals
from django.db import models


class SettingsPortal(models.Model):
    """Модель настроек для портала."""
    user_soap = models.CharField(
        verbose_name='Имя пользователя',
        help_text='Имя пользователя для аутентификации на сервере soap',
        max_length=50,
    )
    passwd_soap = models.CharField(
        verbose_name='Пароль пользователя',
        help_text='Пароль пользователя для аутентификации на сервере soap',
        max_length=255,
    )
    address_soap = models.URLField(
        verbose_name='Адрес сервера',
        help_text='Адрес сервера soap',
    )
    my_company_inn = models.CharField(
        verbose_name='ИНН моей компании',
        help_text='ИНН моей компании для передачи в 1С',
        max_length=20,
        default='2465253470',
    )
    cargo_smart_id = models.PositiveSmallIntegerField(
        verbose_name='ID smart процесса Груз',
        help_text='ID smart процесса, в котором ведется учет грузов',
        default=0,
    )
    number_awb_code = models.CharField(
        verbose_name='Код поля Номер авианакладной',
        help_text='Код поля Номер авианакладной в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1640060552',
    )
    weight_fact_code = models.CharField(
        verbose_name='Код поля Вес фактический',
        help_text='Код поля Вес фактический в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1639712999307',
    )
    weight_pay_code = models.CharField(
        verbose_name='Код поля Вес к оплате',
        help_text='Код поля Вес к оплате в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1639713016989',
    )
    count_position_code = models.CharField(
        verbose_name='Код поля Количество мест',
        help_text='Код поля Количество мест в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1639712970696',
    )
    airline_code = models.CharField(
        verbose_name='Код поля Авиакомпания',
        help_text='Код поля Авиакомпания в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1640060349',
    )
    route_in_code = models.CharField(
        verbose_name='Код поля Пункт отправки',
        help_text='Код поля Пункт отправки в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1662977544',
    )
    route_out_code = models.CharField(
        verbose_name='Код поля Пункт назначения',
        help_text='Код поля Пункт назначения в smart процессе Груз',
        max_length=30,
        default='ufCrm3_1662977599',
    )
    airline_list_id = models.PositiveSmallIntegerField(
        verbose_name='ID универсального списка Авиакомпании',
        help_text='ID универсального списка, в котором находится перечень '
                  'авиакомпаний',
        default=39,
    )
    airline_name_code = models.CharField(
        verbose_name='Код поля Наименование авиакомпании',
        help_text='Код поля Наименование авиакомпании в универсальном списке',
        max_length=30,
        default='PROPERTY_155',
    )
    airline_code_code = models.CharField(
        verbose_name='Код поля Код авиакомпании',
        help_text='Код поля Код авиакомпании в универсальном списке',
        max_length=30,
        default='PROPERTY_157',
    )
    city_list_id = models.PositiveSmallIntegerField(
        verbose_name='ID универсального списка Города',
        help_text='ID универсального списка, в котором находится перечень '
                  'городов',
        default=49,
    )
    city_name_code = models.CharField(
        verbose_name='Код поля Наименование города',
        help_text='Код поля Наименование города в универсальном списке',
        max_length=30,
        default='NAME',
    )
    city_code_code = models.CharField(
        verbose_name='Код поля Код города',
        help_text='Код поля Код города в универсальном списке',
        max_length=30,
        default='PROPERTY_181',
    )
    city_country_code = models.CharField(
        verbose_name='Код поля Страна города',
        help_text='Код поля Страна города в универсальном списке',
        max_length=30,
        default='PROPERTY_183',
    )
    document_number_in_1c_code = models.CharField(
        verbose_name='Код поля Номер заявки в 1С',
        help_text='Код поля Номер заявки в 1С в сделке',
        max_length=30,
        default='UF_CRM_1665034515'
    )
    bill_number_in_1c_code = models.CharField(
        verbose_name='Код поля Номер счета на оплату в 1С',
        help_text='Код поля Номер счета на оплату в 1С в сделке',
        max_length=30,
        default='UF_CRM_1665054060'
    )
    sale_number_in_1c_code = models.CharField(
        verbose_name='Код поля Номер расходной накладной в 1С',
        help_text='Код поля Номер расходной накладной в 1С в сделке',
        max_length=30,
        default='UF_CRM_1665054102'
    )
    invoice_number_in_1c_code = models.CharField(
        verbose_name='Код поля Номер счет фактуры в 1С',
        help_text='Код поля Номер счет фактуры в 1С в сделке',
        max_length=30,
        default='UF_CRM_1665054125'
    )
    link_print_in_1c_code = models.CharField(
        verbose_name='Код поля Ссылка на печатную форму в 1С',
        help_text='Код поля Ссылка на печатную форму в 1С в сделке',
        max_length=30,
        default='UF_CRM_1665054289'
    )
    portal = models.OneToOneField(
        Portals,
        verbose_name='Портал',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Настройка портала'
        verbose_name_plural = 'Настройки портала'

        ordering = ['portal', 'pk']

    def __str__(self):
        return 'Настройки для портала {}'.format(self.portal.name)
