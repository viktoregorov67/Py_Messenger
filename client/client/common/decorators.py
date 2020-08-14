"""Декораторы"""

import sys
import socket
import logging
import log.server_log_config
import log.client_log_config


if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func):
    """Декоратор, выполняющий логирование вызовов функций."""
    def log_save(*args, **kwargs):
        res = func(*args, **kwargs)
        LOGGER.debug(f'Функция {func.__name__} была вызвана из модуля {func.__module__}'
                     f' с параметрами {args}, {kwargs}.')
        return res
    return log_save


def login_required(func):
    """
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    """
    def check(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр Server
        from server.core import Server
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], Server):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            # Проверяем, что передаваемые аргументы не presence
            # сообщение. Если presense, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)
    return check
