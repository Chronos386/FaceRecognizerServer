from datetime import datetime, time
from source_code.utils.week_date_helper import getWeekDayByDate


class SendSchedule:
    def __init__(self, id_: int, date: datetime, time_start: time, time_end: time, group: str, group_id: int,
                 subject: str, subject_id: int, teacher: str, teacher_id: int, room: str, room_id: int, building: str,
                 building_id: int):
        self.id: int = id_
        self.date: datetime = date
        self.weekday: str = getWeekDayByDate(self.date)
        self.time_start: time = time_start
        self.time_end: time = time_end
        self.group: str = group
        self.group_id: int = group_id
        self.subject: str = subject
        self.subject_id: int = subject_id
        self.teacher: str = teacher
        self.teacher_id: int = teacher_id
        self.room: str = room
        self.room_id: int = room_id
        self.building: str = building
        self.building_id: int = building_id

    def toDict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.strftime('%d.%m.%Y'),
            "weekday": self.weekday,
            "time_start": self.time_start.strftime('%H:%M'),
            "time_end": self.time_end.strftime('%H:%M'),
            "group": self.group,
            "group_id": self.group_id,
            "subject": self.subject,
            "subject_id": self.subject_id,
            "teacher": self.teacher,
            "teacher_id": self.teacher_id,
            "room": self.room,
            "room_id": self.room_id,
            "building": self.building,
            "building_id": self.building_id,
        }
