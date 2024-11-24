from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class AccountsDB(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    admin = Column(Boolean, nullable=False)
    email = Column(String(300), nullable=False)
    password = Column(String(300), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.admin} {self.email} {self.password}'
