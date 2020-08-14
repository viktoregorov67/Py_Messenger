import sys
import os
import argparse
import logging
from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

import log.client_log_config
from common.variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.decorators import log
from common.errors import ServerError
from client.database import ClientDatabase
from client.main_window import ClientMainWindow
from client.transport import ClientTransport
from client.start_dialog import UserName

# Инициализация логгера клиента
LOGGER = logging.getLogger('client')


@log
def create_arg_parser():
    """
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов
    адрес сервера, порт, имя пользователя, пароль.
    Выполняет проверку на корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    # Проверяем номер порта
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Запуск сервера с параметром порта {server_port}.'
            f'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    # Проверяем параметры командной строки
    server_address, server_port, client_name, client_passwd = create_arg_parser()
    # Создание клиентского приложения
    client_app = QApplication(sys.argv)
    # Если имя пользователя не было задано, необходимо запросить пользователя.
    start_dialog = UserName()
    if not client_name or not client_passwd:
        client_app.exec_()
        if start_dialog.press_ok:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            LOGGER.debug(
                f'Залогинился пользователь: {client_name}, с паролем: {client_passwd}')
        else:
            sys.exit(0)

    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Загрузка ключей из файла, если ключей нет, то гениерируем пару новую
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.getcwd()
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    keys.publickey().export_key()

    LOGGER.debug('Ключи для клиентов успешно созданы')

    # Инициализация БД
    database = ClientDatabase(client_name)
    # Инициализация сокета и обмен.
    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
        LOGGER.debug('Транспорт готов')
    except ServerError as error:
        print(error.text)
        message = QMessageBox()
        message.critical(
            start_dialog,
            'Ошибка соединения с сервером',
            error.text)
        LOGGER.error(
            f'Ошибка соединения с сервером. Сервер вернул ошибку: {error.text}')
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат программа - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
