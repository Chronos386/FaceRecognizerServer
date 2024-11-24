from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class TeachersDB(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    acc_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name} {self.acc_id} {self.department_id}'
