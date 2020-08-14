# logging - стандартный модуль для организации логирования
import os
import sys
import logging
import logging.config
import logging.handlers
from common.variables import LOGGING_LEVEL

sys.path.append('../')

# Создаем объект форматирования:
SERVER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(message)s')

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
#PATH = os.getcwd()
PATH = os.path.join(PATH, 'server.log')

# Создаем файловый обработчик логирования (можно задать кодировку):
SERVER_FILE_LOG = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
SERVER_FILE_LOG.setFormatter(SERVER_FORMATTER)
steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(SERVER_FORMATTER)
steam.setLevel(logging.INFO)

# Создаем объект-логгер
LOGGER = logging.getLogger('server')

# Добавляем в логгер новый обработчик событий и устанавливаем уровень логирования
LOGGER.addHandler(SERVER_FILE_LOG)
LOGGER.setLevel(LOGGING_LEVEL)
LOGGER.addHandler(steam)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
