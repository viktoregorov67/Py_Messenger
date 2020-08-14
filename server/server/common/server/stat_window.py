from PyQt5.QtWidgets import QDialog, QPushButton, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class HistoryWindow(QDialog):
    """
    Класс - окно со статистикой пользователей
    """
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle('Статистика пользователей')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)
        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.create_stat_model()

    def create_stat_model(self):
        """
        Функция реализующая заполнение таблицы
        с историей (статистикой) сообщений
        """
        # Список записей из базы
        history_list = self.database.message_history()
        # Объект модели данных:
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ['Имя пользователя', 'Дата последнего входа', 'Отправлено сообщений', 'Принято сообщений'])
        for row in history_list:
            user, last_login, send, recieve = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_login = QStandardItem(str(last_login.replace(microsecond=0)))
            last_login.setEditable(False)
            send = QStandardItem(str(send))
            send.setEditable(False)
            recieve = QStandardItem(str(recieve))
            recieve.setEditable(False)
            list.appendRow([user, last_login, send, recieve])
        self.history_table.setModel(list)
        self.history_table.resizeColumnsToContents()
        self.history_table.resizeRowsToContents()
