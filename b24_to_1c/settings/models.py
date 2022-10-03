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
