class SendTeacherAttendance:
    def __init__(self, teacher_id: int, teacher_name: str, attendance_percent: float, total_classes: int):
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.attendance_percent = attendance_percent
        self.total_classes = total_classes

    def toDict(self) -> dict:
        return {
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "attendance_percent": round(self.attendance_percent, 2),
            "total_classes": self.total_classes
        }