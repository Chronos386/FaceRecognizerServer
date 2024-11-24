from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class InstitutesDB(Base):
    __tablename__ = 'institutes'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name}'
