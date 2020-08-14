import datetime

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.sql import default_comparator


class ServerDatabase:
    '''
    Класс - оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    '''

    class AllUsers:
        """Класс - отображение таблицы всех пользователей"""

        def __init__(self, username, passwd_hash):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.public_key = None
            self.id = None

    class ActiveUsers:
        """Класс - отображение таблицы активных пользователей"""

        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        """Класс - отображение таблицы истории логирования"""

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UserContactList:
        """Класс - отображение таблицы контактов пользователей"""

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory:
        """Класс отображение таблицы истории действий"""

        def __init__(self, user):
            self.id = None
            self.user = user
            self.send = 0
            self.accepted = 0

    def __init__(self, path):
        # Создаём движок базы данных
        print(path)
        self.database_engine = create_engine(
            f'sqlite:///{path}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})
        self.metadata = MetaData()
        # Создаём таблицу пользователей
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('passwd_hash', String),
                            Column('public_key', Text)
                            )
        # Создаём таблицу активных пользователей
        active_users_table = Table(
            'Active_users', self.metadata, Column(
                'id', Integer, primary_key=True), Column(
                'user', ForeignKey('Users.id'), unique=True), Column(
                'ip_address', String), Column(
                    'port', Integer), Column(
                        'login_time', DateTime))
        # Создаём таблицу истории входов
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )
        # Создаём таблицу контактов пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Создаём таблицу истории пользователей
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('send', Integer),
                                    Column('accepted', Integer)
                                    )

        # Создание таблиц
        self.metadata.create_all(self.database_engine)
        # Создание отображений
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UserContactList, contacts)
        mapper(self.UsersHistory, users_history_table)
        # Создание сессии
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # При входе пользователя проверяем если пользователь есть, записываем в базу факт входа,
    # если нет, то создаем нового пользователя в БД и фиксируем факт входа
    def user_login(self, username, ip_address, port, key):
        """
        Метод выполняющийся при входе пользователя, записывает в базу факт входа
        Обновляет открытый ключ пользователя при его изменении.
        """
        is_user_exist = self.session.query(
            self.AllUsers).filter_by(
            name=username)
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # и проверяем корректность ключа
        if is_user_exist.count():
            user = is_user_exist.first()
            user.last_login = datetime.datetime.now()
            if user.public_key != key:
                user.public_key = key
        else:
            raise ValueError('Пользователь не зарегистрирован')

        # Создаем запись в таблицу активных пользователей о факте входа
        new_active_user = self.ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(
            user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    # Если пользователь вышел, удаляем его из таблицы активных пользователей
    def user_logout(self, username):
        """Метод фиксирующий отключения пользователя."""
        user = self.session.query(
            self.AllUsers).filter_by(
            name=username).first()

        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    # Функция регистрации пользователя в базе
    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.AllUsers(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    # Функция удаления пользователя из базы
    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(
            self.UserContactList).filter_by(
            user=user.id).delete()
        self.session.query(
            self.UserContactList).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(name=name).delete()
        self.session.commit()

    # Функция получения хэша пароля
    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.passwd_hash

    # Функция получения публичного ключа пользователя
    def get_public_key(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.public_key

    # Функция проверки существования пользователя
    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.AllUsers).filter_by(name=name).count():
            return True
        else:
            return False

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в
    # БД
    def process_message(self, sender, recipient):
        """Метод записывающий в таблицу статистики факт передачи сообщения."""
        # Получение ID отправителя и получателя
        sender = self.session.query(
            self.AllUsers).filter_by(
            name=sender).first().id
        recipient = self.session.query(
            self.AllUsers).filter_by(
            name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(
            self.UsersHistory).filter_by(
            user=sender).first()
        sender_row.send += 1
        recipient_row = self.session.query(
            self.UsersHistory).filter_by(
            user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # Функция добавления контактов пользователя
    def add_contact(self, user, contact):
        """Метод добавления контакта для пользователя."""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(
            self.AllUsers).filter_by(
            name=contact).first()

        if not contact or self.session.query(
                self.UserContactList).filter_by(
                user=user.id,
                contact=contact.id).count():
            return

        contact_list = self.UserContactList(user.id, contact.id)
        self.session.add(contact_list)
        self.session.commit()

    # Функция удаления контактов пользователя
    def remove_contact(self, user, contact):
        """Метод удаления контакта пользователя."""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(
            self.AllUsers).filter_by(
            name=contact).first()
        # Проверяем что контакт может существовать
        if not contact:
            return
        # Удаляем
        self.session.query(self.UserContactList).filter(
            self.UserContactList.user == user.id,
            self.UserContactList.contact == contact.id).delete()
        self.session.commit()

    # Функция возвращает список известных пользователей со временем последнего
    # входа.
    def users_list(self):
        """Метод возвращающий список известных пользователей со временем последнего входа."""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login)
        return query.all()

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        """Метод возвращающий список активных пользователей."""
        query = self.session.query(self.AllUsers.name,
                                   self.ActiveUsers.ip_address,
                                   self.ActiveUsers.port,
                                   self.ActiveUsers.login_time
                                   ).join(self.AllUsers)
        return query.all()

    # Функция возвращающаяя историю входов по пользователю или всем
    # пользователям
    def login_history(self, username=None):
        """Метод возвращающий историю входов"""
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        """Метод возвращающий список контактов пользователя."""
        # Запрашивааем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        # Запрашиваем его список контактов
        query = self.session.query(
            self.UserContactList,
            self.AllUsers.name). filter_by(
            user=user.id). join(
            self.AllUsers,
            self.UserContactList.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        """Метод возвращающий статистику сообщений."""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.send,
            self.UsersHistory.accepted).join(
            self.AllUsers)
        return query.all()


if __name__ == '__main__':
    test_db = ServerDatabase()
    test_db.user_login('test_user_1', '192.168.32.17', 7779)
    test_db.user_login('test_user_2', '192.168.38.123', 7777)

    print(test_db.users_list())
    print(test_db.active_users_list())

    test_db.user_logout('test_user_1')
    print(test_db.active_users_list())

    test_db.login_history('test_user_1')
    print(test_db.users_list())
    test_db.add_contact('test_user_2', 'test_user_1')
    test_db.add_contact('test_user_2', 'test_user_3')
    test_db.add_contact('test_user_1', 'test_user_4')
    print(test_db.remove_contact('test_user_1'))
    test_db.remove_contact('test_user_1', 'test_user_4')
    print(test_db.remove_contact('test_user_1'))
    test_db.process_message('test_user_1', 'test_user_2')
    print(test_db.message_history())
    print()
    print(test_db.remove_contact('test_user_2'))
