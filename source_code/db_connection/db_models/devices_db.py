from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class DevicesDB(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.room_id}'
