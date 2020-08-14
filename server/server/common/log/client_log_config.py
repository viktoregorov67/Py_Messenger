# logging - стандартный модуль для организации логирования
import sys
import os
import logging
import logging.config
from common.variables import LOGGING_LEVEL
sys.path.append('../')


# Создаем объект форматирования:
CLIENT_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(message)s')

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
#PATH = os.getcwd()
PATH = os.path.join(PATH, 'client.log')

# Создаем файловый обработчик логирования (можно задать кодировку):
CLIENT_FILE_LOG = logging.FileHandler(PATH, encoding='utf-8')
CLIENT_FILE_LOG.setFormatter(CLIENT_FORMATTER)
steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(CLIENT_FORMATTER)
steam.setLevel(logging.INFO)
# Создаем объект-логгер
LOGGER = logging.getLogger('client')

# Добавляем в логгер новый обработчик событий и устанавливаем уровень логирования
LOGGER.addHandler(CLIENT_FILE_LOG)
LOGGER.setLevel(LOGGING_LEVEL)
LOGGER.addHandler(steam)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
