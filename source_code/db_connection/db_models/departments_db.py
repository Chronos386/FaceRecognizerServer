from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class DepartmentsDB(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    institute_id = Column(Integer, ForeignKey('institutes.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name} {self.institute_id}'
