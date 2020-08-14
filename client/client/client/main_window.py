import base64
import sys
import json
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from client.main_window_ui import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog

from common.errors import ServerError
from common.variables import MESSAGE_TEXT, SENDER

sys.path.append('../')
LOGGER = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """
    Класс - основное окно пользователя.
    Содержит всю основную логику работы клиентского модуля.
    Конфигурация окна создана в QTDesigner и загружается из
    конвертированого файла main_window_ui.py
    """
    def __init__(self, database, transport, keys):
        super().__init__()
        # Основные переменные
        self.database = database
        self.transport = transport
        # объект - дешифорвщик сообщений с предзагруженным ключём
        self.decrypter = PKCS1_OAEP.new(keys)
        # Загрузка конфигурации из дизайнера
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)
        # Кнопка выход
        self.ui.menu_exit.triggered.connect(qApp.exit)
        # Кнопка отправки сообщения
        self.ui.btn_send.clicked.connect(self.send_message)
        # Кнопки добавления контакта
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        # Кнопки удаления контакта
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)
        # Дополнительные атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.contact_list_update()
        self.disable_input()
        self.show()

    def disable_input(self):
        """Функция делающая неактивным поле ввода и кнопки отправки"""
        self.ui.label_new_message.setText('Выберите получателя, дважды кликнув на нем в окне контактов')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_send.setDisabled(True)
        self.ui.btn_clear.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def history_list_update(self):
        """
        Функция заполняющая текущий диалог
        историей переписки с текущим собеседником.
        """
        # История сообщений, отсортированная по дате
        list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        # Если модель не создана
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)

        # Очищаем от старых записей
        self.history_model.clear()
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20

        # Заполнение модели записями
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """Функция обработки двойного клика"""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # Вызов основной функции
        self.set_active_user()

    def set_active_user(self):
        """Функция активации чата с собеседником"""
        # Запрашиваем публичный ключ пользователя и создаём объект шифрования
        try:
            self.current_chat_key = self.transport.key_request(self.current_chat)
            LOGGER.debug(f'Загружен ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            LOGGER.debug(f'Не удалось загрузить ключ для {self.current_chat}')

        # Если ключа нет то ошибка, что не удалось начать чат с пользователем
        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        self.ui.label_new_message.setText(f'Введите сообщение для {self.current_chat}: ')
        self.ui.btn_send.setDisabled(False)
        self.ui.btn_clear.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        # Выводим историю по данному пользователю
        self.history_list_update()

    def contact_list_update(self):
        """Функция обновления листа контактов"""
        contact_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contact_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """
        Функция добавления контактов.
        Запускает диалоговое окно для добавления контакта
        """
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """
        Функция обработчик добавления контакта.
        Обновляет таблицу и список контактов
        """
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """
        Функция добавляющая контакт в серверную и клиентсткую BD.
        После обновления баз данных обновляет и содержимое окна.
        """
        try:
            self.transport.add_contact(new_contact)
        except ServerError as e:
            self.messages.critical(self, 'Ошибка сервера', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            LOGGER.info(f'Добавлен контакт: {new_contact}')
            self.messages.information(self, 'ОК', 'Контакт успешно добавлен.')

    def delete_contact_window(self):
        """
        Функция удаления контакта.
        Запускает диалоговое окно для удаления контакта
        """
        global remove_dialog
        remove_dialog = DelContactDialog(self.transport, self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.adelete_contact(remove_dialog))
        remove_dialog.show()

    # Обработчик удаления контакта, обновляет таблицу и список контактов
    def delete_contact(self, item):
        """
        Функция удаляет контакт из серверной и клиентсткой BD.
        После обновления баз данных обновляет и содержимое окна.
        """
        select_contact = item.selector.currentText()
        try:
            self.transport.remove_contact(select_contact)
        except ServerError as e:
            self.messages.critical(self, 'Ошибка сервера', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        else:
            self.database.del_contact(select_contact)
            self.contact_list_update()
            LOGGER.info(f'Удален контакт: {select_contact}')
            self.messages.information(self, 'ОК', 'Контакт успешно добавлен.')
            item.close()
            if select_contact == self.current_chat:
                self.current_chat = None
                self.disable_input()

    def send_message(self):
        """
        Функция отправки сообщения текущему собеседнику.
        Реализует шифрование сообщения и его отправку.
        """
        # Проверка поля на пустоту. Если поле не пустое, то забираем сообщение и очищаем поле
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf8'))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
        try:
            self.transport.send_message(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as e:
            self.messages.critical(self, 'Ошибка сервера', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            LOGGER.debug(f'Отравлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(str)
    def message(self, message):
        """
        Слот обработчик поступаемых сообщений, выполняет дешифровку
        поступаемых сообщений и их сохранение в истории сообщений.
        Запрашивает пользователя если пришло сообщение не от текущего
        собеседника. При необходимости меняет собеседника.
        """
        encrypted_message = base64.b64encode(message[MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(self, 'Ошибка', 'Не удалось декодировать сообщение')
            return
        self.database.save_message(self.current_chat, 'in', decrypted_message.decode('utf8'))

        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверяем наличие пользователя в контактах
            if self.database.check_contact(sender):
                # Если есть, спрашиваем и желании открыть с ним чат и открываем
                if self.messages.question(self, 'У Вас новое сообщение',\
                                          f'Получено сообщение от {sender}, начать чат?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                if self.messages.question(self, 'У Вас новое сообщение',\
                                          f'Получено сообщение от {sender}. \n '
                                          f'Пользователя нет в списке контактов. \n '
                                          f'Добавить пользователя в контакты и начать чат?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.database.save_message(self.current_chat, 'in', decrypted_message.decode('utf8'))
                    self.set_active_user()

    # В случае потери соединения
    @pyqtSlot()
    def connection_lost(self):
        """
        Слот обработчик потери соеднинения с сервером.
        Выдаёт окно предупреждение и завершает работу приложения.
        """
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером')
        self.close()

    @pyqtSlot()
    def signal_205(self):
        """
        Слот выполняющий обновление баз данных по команде сервера.
        """
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(self, 'Упс...', 'Пользователь был удален с сервера')
            self.disabled_input()
            self.current_chat = None
        self.contact_list_update()

    def make_connection(self, trans_obj):
        """Функция обеспечивающая соединение сигналов и слотов."""
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
