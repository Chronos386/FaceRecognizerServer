from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class AttendanceDB(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    status = Column(Boolean, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedule.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.status} {self.student_id} {self.schedule_id}'
