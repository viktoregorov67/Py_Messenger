from PyQt5.QtWidgets import QDialog, QPushButton, QApplication, QLabel, qApp, QLineEdit


class UserName(QDialog):
    """
    Класс реализующий стартовый диалог с запросом логина и пароля
    пользователя.
    """
    def __init__(self):
        super().__init__()

        self.press_ok = False

        self.setFixedSize(180, 140)
        self.setWindowTitle('Ввод имени')

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(155, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Войти', self)
        self.btn_ok.move(10, 105)
        self.btn_ok.clicked.connect(self.check_click)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.move(90, 105)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.label_passwd = QLabel('Введите пароль:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.show()

    # Проверяем заполнение поля
    def check_click(self):
        """Функция обработки нажатия кнопки ОК."""
        if self.client_name.text() and self.client_passwd.text():
            self.press_ok = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserName()
    app.exec_()
