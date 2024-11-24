from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class HashesDB(Base):
    __tablename__ = 'hashes'
    id = Column(Integer, primary_key=True)
    hash = Column(String(30), nullable=False)
    date = Column(Date, nullable=False)
    acc_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.hash} {self.date} {self.acc_id}'
