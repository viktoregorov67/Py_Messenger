from setuptools import setup, find_packages

setup(name="mess_client_skif",
      version="0.0.1",
      description="Messenger_Client",
      author="Egorov Viktor",
      author_email="seal_skif@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
