from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class RoomsDB(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    number = Column(String(300), nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.number} {self.building_id}'
