Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

Скрипт decorators.py
---------------------

.. automodule:: common.decorators
	:members:
	
Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.Port
    :members:

.. autoclass:: common.descriptors.Address
    :members:
   
Скрипт errors.py
---------------------
   
.. autoclass:: common.errors.IncorrectDataRecivedError
   :members:

.. autoclass:: common.errors.ServerError
   :members:

.. autoclass:: common.errors.NonDictInputError
   :members:

.. autoclass:: common.errors.ReqFieldMissingError
   :members:
   
Скрипт metaclasses.py
-----------------------

.. autoclass:: common.metaclasses.ServerVerifier
   :members:
   
.. autoclass:: common.metaclasses.ClientVerifier
   :members:
   
Скрипт utils.py
---------------------

common.utils. **get_message** (client)


	Функция приёма сообщений от удалённых компьютеров. Принимает сообщения JSON,
	декодирует полученное сообщение и проверяет что получен словарь.

common.utils. **send_message** (sock, message)


	Функция отправки словарей через сокет. Кодирует словарь в формат JSON и отправляет через сокет.


Скрипт variables.py
---------------------

Содержит разные глобальные переменные проекта.