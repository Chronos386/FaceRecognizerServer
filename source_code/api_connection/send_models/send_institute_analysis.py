class SendInstituteAnalysis:
    def __init__(self, institute_id: int, name: str, attendance_percent: float):
        self.institute_id = institute_id
        self.name = name
        self.attendance_percent = attendance_percent

    def toDict(self) -> dict:
        return {
            "institute_id": self.institute_id,
            "name": self.name,
            "attendance_percent": round(self.attendance_percent, 2)
        }