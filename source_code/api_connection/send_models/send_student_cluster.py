class SendStudentCluster:
    def __init__(self, student_id: int, student_name: str, attendance_percent: float, cluster: str):
        self.student_id = student_id
        self.student_name = student_name
        self.attendance_percent = attendance_percent
        self.cluster = cluster

    def toDict(self) -> dict:
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "attendance_percent": round(self.attendance_percent, 2),
            "cluster": self.cluster
        }