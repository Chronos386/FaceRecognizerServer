class SendGroupAttendance:
    def __init__(self, group_id: int, group_name: str, attendance_percent: float, total_attendance: int):
        self.group_id = group_id
        self.group_name = group_name
        self.attendance_percent = attendance_percent
        self.total_attendance = total_attendance

    def toDict(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "attendance_percent": round(self.attendance_percent, 2),
            "total_attendance": self.total_attendance
        }
