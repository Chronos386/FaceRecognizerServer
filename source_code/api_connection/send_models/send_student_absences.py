class SendStudentAbsences:
    def __init__(self, student_id: int, student_name: str, absences_count: int, group_name: str):
        self.student_id = student_id
        self.student_name = student_name
        self.absences_count = absences_count
        self.group_name = group_name

    def toDict(self) -> dict:
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "absences_count": self.absences_count,
            "group": self.group_name
        }