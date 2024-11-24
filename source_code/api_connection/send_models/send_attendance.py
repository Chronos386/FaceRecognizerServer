class SendAttendance:
    def __init__(self, id_: int, status: bool, student_id: int, schedule_id: int):
        self.id = id_
        self.status = status
        self.student_id = student_id
        self.schedule_id = schedule_id

    def toDict(self) -> dict:
        data = {
            "id": self.id,
            "status": self.status,
            "student_id": self.student_id,
            "schedule_id": self.schedule_id
        }
        return data
