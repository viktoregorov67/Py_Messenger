import sys
import logging

from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt

sys.path.append('../')

LOGGER = logging.getLogger('client')


class AddContactDialog(QDialog):
    """
    Добавление пользователя в список контактов.
    Предлагает пользователю список возможных контактов и
    добавляет выбранный в контакты.
    """
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(330, 120)
        self.setWindowTitle('Добавление контакта')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Обновить список', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(70, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(70, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        # Заполняем список возможных контактов
        self.possible_contacts_update()
        # Назначаем действие на кнопку обновить
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self):
        """
        Функция заполнения списка возможных контактов.
        Создаёт список всех зарегистрированных пользователей
        за исключением уже добавленных в контакты и самого себя.
        """
        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        # далим сами себя из списка
        users_list.remove(self.transport.username)
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        """
        Функция обновления списка возможных контактов. Запрашивает с сервера
        список известных пользователей и обносляет содержимое окна.
        """
        try:
            self.transport.user_list_request()
        except OSError:
            pass
        else:
            LOGGER.debug('Обновление списка контактов с сервера выполнено')
            self.possible_contacts_update()
