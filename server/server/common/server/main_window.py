import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp,  QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
from server.stat_window import HistoryWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.remove_user import DeleteUser



class MainWindow(QMainWindow):
    """ Класс - основное окно сервера. """
    def __init__(self, database, server, config):
        super().__init__()
        # База данных сервера
        self.database = database

        self.server_thread = server
        self.config = config

        # кнопка выход
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+X')
        self.exitAction.triggered.connect(qApp.quit)
        # кнопка настройки сервера
        self.config_button = QAction('Настройки сервера', self)
        # кнопка обновления списка клиентов
        self.refresh_button = QAction('Обновление списка', self)
        # кнопка истории сообщений
        self.show_history_button = QAction('История пользователей', self)

        # Кнопка регистрации пользователя
        self.register_button = QAction('Регистрация пользователя', self)

        # Кнопка удаления пользователя
        self.remove_button = QAction('Удаление пользователя', self)

        # Статусбар
        self.statusBar()
        self.statusBar().showMessage('Сервер запущен')
        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.register_button)
        self.toolbar.addAction(self.remove_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(self.exitAction)

        # настройка вида основного окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Message server')

        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)
        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Таймер, обновляющий список клиентов 1 раз в секунду
        self.timer = QTimer()
        self.timer.timeout.connect(self.create_gui_model)
        self.timer.start(1000)

        # Связываем кнопки с процедурами
        self.refresh_button.triggered.connect(self.create_gui_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_button.triggered.connect(self.server_config)
        self.register_button.triggered.connect(self.reg_user)
        self.remove_button.triggered.connect(self.rem_user)

        # Отображаем окно.
        self.show()

    def create_gui_model(self):
        """Функция заполняющая таблицу активных пользователей."""
        users_list_active = self.database.active_users_list()
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(['Имя пользователя', 'IP адрес', 'Порт', 'время подключения'])
        for row in users_list_active:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(list)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Метод создающий окно со статистикой клиентов."""
        global history_window
        history_window = HistoryWindow(self.database)
        history_window.show()

    def server_config(self):
        """Метод создающий окно с настройками сервера."""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """Метод создающий окно регистрации пользователя"""
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        """"Метод создающий окно удаления пользователя."""
        global rem_window
        rem_window = DeleteUser(self.database, self.server_thread)
        rem_window.show()
