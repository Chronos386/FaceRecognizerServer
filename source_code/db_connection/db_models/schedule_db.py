from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class ScheduleDB(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    time_start = Column(Time, nullable=False)
    time_end = Column(Time, nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.date} {self.time_start} {self.time_end} {self.group_id} {self.subject_id} {self.teacher_id} {self.room_id}'
