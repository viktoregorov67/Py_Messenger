import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
from common.metaclasses import ServerVerifier
from common.descriptors import Port, Address
from common.utils import get_message, send_message
from common.decorators import login_required
from common.variables import MAX_CONNECTIONS, DESTINATION, SENDER, PRESENCE, TIME, USER, ACTION, ACCOUNT_NAME, \
    RESPONSE_200, RESPONSE_400, ERROR, MESSAGE, MESSAGE_TEXT, EXIT, GET_CONTACTS, RESPONSE_202, LIST_INFO, \
    REMOVE_CONTACT, USERS_REQUEST, PUBLIC_KEY_REQUEST, RESPONSE_511, DATA, RESPONSE, PUBLIC_KEY, RESPONSE_205, \
    ADD_CONTACT

# Инициализация логгера сервера
LOGGER = logging.getLogger('server')


class Server(threading.Thread):
    """
    Основной класс сервера. Принимает содинения, словари - пакеты
    от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    """
    # Дескриптор порта и ip адреса
    port = Port()
    address = Address()

    def __init__(self, listen_address, listen_port, database):
        # Параментры подключения
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.database = database
        # Сокет, через который будет осуществляться работа
        self.main_socket = None
        # Устанавливаем список клиентов и очередь сообщений
        self.clients = []
        # Сокеты
        self.listen_sockets = None
        self.error_sockets = None
        # Флаг продолжения работы
        self.running = True
        # Словарь имен пользователей и соответствующие им сокеты
        self.names = dict()
        # Конструктор предка
        super().__init__()

    def run(self):
        """Метод основной цикл потока"""

        self.start_socket()

        # Основной цикл программы сервера
        while self.running:
            try:
                client, client_address = self.main_socket.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Клиент {client_address} подключился.')
                client.settimeout(5)
                self.clients.append(client)

            recv_lst = []
            send_lst = []
            err_lst = []

            # Проверка на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as e:
                LOGGER.error(f'Ошибка сокетов: {e}')

            # Принимаем сообщения и если они есть, то заполняем словарь, если
            # ошибка - отключаем клиента
            if recv_lst:
                for client_with_msg in recv_lst:
                    try:
                        self.process_client_message(get_message(client_with_msg), client_with_msg)
                    except (OSError, json.JSONDecodeError, TypeError) as e:
                        LOGGER.debug(f'Получение данных из исключения клиента.', exc_info=e)
                        self.clients.remove(client_with_msg)

    def start_socket(self):
        """Метод инициализатор сокета."""
        LOGGER.info(
            f'Сервер запущен. Порт для подключений: {self.listen_port}.'
            f'Адрес с котрого принимаются сообщения: {self.listen_address}. '
        )
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.listen_address, self.listen_port))
        transport.settimeout(0.5)
        # Слушаем порт
        self.main_socket = transport
        self.main_socket.listen(MAX_CONNECTIONS)

    def remove_client(self, client):
        """
        Функция обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        :param client:
        :return:
        """
        LOGGER.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def process_message(self, message):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                LOGGER.info(
                    f'Отправлено сообщение пользователю {message[DESTINATION]} '
                    f'от пользователя {message[SENDER]}.')
            except OSError:
                self.remove_client(self.names[message[DESTINATION]])

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listen_sockets:
            LOGGER.error(
                f'Связь с пользователем {message[DESTINATION]} потеряна. '
                f'Соединение закрыто, отправка сообщения невозможна.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    @login_required
    def process_client_message(self, message, client):
        """ Обработчик сообщений от клиентов """
        LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если сообщение о присутствии то вызываем функцию авторизации.
            self.autorized_user(message, client)

        # Если это сообщение, то добавляем его в очередь
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and DESTINATION in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message and \
                self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)
            LOGGER.info(f'Клиент {message[ACCOUNT_NAME]} коректно вышел')

        # Если запрос контактов
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если запрос на добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если запрос на удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если запрос публичного ключа пользователя
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_public_key(message[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Публичный ключ не найден для данного пользователя.'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorized_user(self, message, client):
        """
        Функция реализующая авторизацию пользователей.
        :param message:
        :param client:
        :return:
        """

        # Если имя пользователя уже занято то возвращаем 400
        LOGGER.debug(f'Авторизация для пользователя: {message[USER]}')

        if message[USER][ACCOUNT_NAME] not in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                LOGGER.debug(f'Имя занято {response}')
                send_message(client, response)
            except OSError:
                LOGGER.debug(f'Ошибка системы')
                pass
            self.clients.remove(client)
            client.close()

        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                LOGGER.debug(f'Неизвестное имя пользователя {response}')
                send_message(client, response)
            except OSError:
                pass
            self.clients.remove(client)
            client.close()
        else:
            LOGGER.debug('Имя пользователя корректно. Проверяем пароль.')
            # Словарь - заготовка
            message_auth = RESPONSE_511
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем
            # серверную версию ключа
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str)
            digest = hash.digest()
            LOGGER.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_message(client, message_auth)
                ans = get_message(client)
            except OSError as err:
                LOGGER.debug('Ошибка авторизации:', exc_info=err)
                client.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            # Если ответ клиента корректный, то сохраняем его в список
            # пользователей.
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                # сохраняем новый
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
                self.clients.remove(client)
                client.close()

    def service_update_lists(self):
        """
        Функция реализующая отправку сервисного сообщения "205" клиентам.
        :return:
        """
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
