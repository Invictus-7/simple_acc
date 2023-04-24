import os
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, declared_attr, Session

load_dotenv()


class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


AlchemyBase = declarative_base(cls=Base)

engine = create_engine(
     f'{os.getenv("DB_ENG")}://{os.getenv("DB_NAME")}:{os.getenv("DB_PASS")}'
     f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_USER")}', echo=False)

AlchemyBase.metadata.create_all(engine)
session = Session(engine)


class BaseTransaction(AlchemyBase):
    """Абстрактный класс для создания
    двух разных таблиц."""
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    currency = Column(String(30))
    volume = Column(Integer)

    def __str__(self):
        return f'Перевод на сумму {self.volume} {self.currency} совершил {self.name}'


class UsualTransaction(BaseTransaction):
    """Используется для записи данных в таблицу,
    которая хранит сведения об операциях на сумму
    меньше, либо равную 1000 рублей."""
    pass


class BigTransaction(BaseTransaction):
    """Используется для записи данных в таблицу,
    которая хранит сведения об операциях на сумму
    больше 1000 рублей."""
    pass
