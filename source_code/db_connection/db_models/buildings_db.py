from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class BuildingsDB(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    address = Column(String(500), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name} {self.address}'
