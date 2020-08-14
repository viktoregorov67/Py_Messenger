import os
import sys
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.sql import default_comparator
from common.variables import *
import datetime
sys.path.append('../')


class ClientDatabase:
    """
    Класс - оболочка для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    """
    class KnownUsers:
        """Класс - отображение таблицы известных пользователей."""

        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        """Класс - отображение таблицы истории сообщений"""

        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        """Класс - отображение списка контактов"""

        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Конструктор класса:
    def __init__(self, name):
        # Создаём движок базы данных, т.к. разрешено несколько клиентов
        # одновременно, каждый должен иметь свою БД
        #path = os.path.dirname(os.path.realpath(__file__))
        path = os.getcwd()
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(
            f'sqlite:///{os.path.join(path, filename)}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})

        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаём таблицу известных пользователей
        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        # Создаём таблицу истории сообщений
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('contact', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        # Создаём таблицу контактов
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они
        # подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """Функция добавления контактов"""
        if not self.session.query(
                self.Contacts).filter_by(
                name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """Функция удаления контакта"""
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def contacts_clear(self):
        """Метод очищающий таблицу со списком контактов."""
        self.session.query(self.Contacts).delete()

    def add_users(self, users_list):
        """
        Функция добавления известных пользователей.
        Пользователи получаются только с сервера, поэтому таблица очищается.
        """
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, contact, direction, message):
        """Функция сохраняющяя сообщения в БД"""
        message_row = self.MessageHistory(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """Функция возвращающая список всех контактов."""
        return [contact[0]
                for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """Функция возвращающяя список известных пользователей"""
        return [user[0]
                for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        """Функция проверяющяя наличие пользователя в известных"""
        if self.session.query(
                self.KnownUsers).filter_by(
                username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """Функция проверяющяя существование контакта"""
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        """Функция возвращающая историю переписки с определенным пользователем"""
        query = self.session.query(
            self.MessageHistory).filter_by(
            contact=contact)
        return [(history_row.contact,
                 history_row.direction,
                 history_row.message,
                 history_row.date) for history_row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('test_User_2')
    # for i in ['test_User_3', 'test_User_4', 'test_User_5']:
    #     test_db.add_contact(i)
    # test_db.add_contact('test_User_4')
    # test_db.add_users(['test_User_1', 'test_User_2', 'test_User_3', 'test_User_4', 'test_User_5'])
    # test_db.save_message('test_User_1', 'test_User_2', f'Тестовое сообщение от {datetime.datetime.now()}!')
    # test_db.save_message('test_User_2', 'test_User_1', f'Ответ на тестовое сообщение от {datetime.datetime.now()}!')
    # print(test_db.get_contacts())
    # print(test_db.get_users())
    # print(test_db.check_user('test_User_1'))
    # print(test_db.check_user('test_User_20'))
    # print(test_db.get_history('test_User_2'))
    # print(test_db.get_history(to_who='test_User_2'))
    # print(test_db.get_history('test_User_3'))
    # test_db.del_contact('test_User_4')
    # print(test_db.get_contacts())
