from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class StudentsDB(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    acc_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name} {self.acc_id} {self.group_id}'
