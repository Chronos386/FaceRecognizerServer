from datetime import date


class AttendanceDailyDynamic:
    def __init__(self, date_: date, attendance_per: float, attended: int, total: int):
        self.date = date_
        self.attendance_per = attendance_per
        self.attended = attended
        self.total = total

    def toDict(self) -> dict:
        return {
            "date": self.date.strftime('%d.%m.%Y'),
            "attendance_per": round(self.attendance_per, 2),
            "attendance": f"{round(self.attendance_per, 1)}% ({self.attended}/{self.total})"
        }