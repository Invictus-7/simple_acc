from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, declared_attr, Session


class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


AlchemyBase = declarative_base(cls=Base)

# как правильно создать движок для запуска на Ubuntu c PSQL?
engine = create_engine('postgresql://postgres:postgres@localhost:5432/transactions', echo=False)
# можно запустить postgre в докере для локальной работы, а второй - будет на сервере
AlchemyBase.metadata.create_all(engine)
session = Session(engine)


class BaseTransaction(AlchemyBase):
    """Abstract class for two tables."""
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    currency = Column(String(30))
    volume = Column(Integer)

    def __str__(self):
        return f'Перевод на сумму {self.volume} {self.currency} совершил {self.name}'


class UsualTransaction(BaseTransaction):
    """Maps to table with transaction
    amounts less than 1000 RUR."""
    pass


class BigTransaction(BaseTransaction):
    """Maps to table with transaction
    amounts greater than 1000 RUR."""
    pass


