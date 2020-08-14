import logging
import ipaddress
import sys

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


class Port:
    """
    Класс - дескриптор для номера порта.
    Позволяет использовать только порты с 1023 по 65536.
    При попытке установить неподходящий номер порта генерирует исключение.
    """
    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            LOGGER.critical(
                f'Запуск сервера с параметром порта {value}.'
                f'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
            sys.exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class Address:
    """
    Класс - дескриптор для ip-адреса.
    Проверяет адрес на корректность.
    При попытке ввода невалидного ip-адреса генерирует исключение.
    """
    def __set__(self, instance, value):
        if value:
            try:
                ipv4 = ipaddress.ip_address(value)
            except ValueError as e:
                LOGGER.critical(f'Некорректно указан ip адрес {value}.')
                sys.exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
