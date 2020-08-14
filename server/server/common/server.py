import configparser
import os
import sys
import logging
import argparse
import log.server_log_config
from common.decorators import log
from common.variables import DEFAULT_PORT
from server.core import Server
from server.server_database import ServerDatabase
from server.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Инициализация логгера сервера
LOGGER = logging.getLogger('server')


@log
def create_arg_parser(default_address, default_port):
    """ Парсер аргументов коммандной строки """
    LOGGER.debug(
        f'Инициализация парсера аргументов коммандной строки: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', default=default_address, nargs='?')
    parser.add_argument(
        '-p',
        '--port',
        default=default_port,
        type=int,
        nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.addr
    listen_port = namespace.port
    gui_flag = namespace.no_gui
    return listen_address, listen_port, gui_flag


@log
def config_load():
    """ Парсер конфигурационного ini файла. """
    config = configparser.ConfigParser()

    #dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по
    # умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_base.db3')
        return config


@log
def main():
    """ Основная функция сервера"""
    # Загружаем файл конфигурации
    config = config_load()

    # Проверяем параметры командной строки
    listen_address, listen_port, gui_flag = create_arg_parser(
        config['SETTINGS']['Listen_Address'], config['SETTINGS']['Default_port'])

    database = ServerDatabase(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера и его запуск:
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break
    else:
        # Графическое окружение сервера
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        # Запуск графического интерфейса
        server_app.exec_()
        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
