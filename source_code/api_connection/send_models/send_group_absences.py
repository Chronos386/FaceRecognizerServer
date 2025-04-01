class SendGroupAbsences:
    def __init__(self, group_id: int, group_name: str, absences_count: int):
        self.group_id = group_id
        self.group_name = group_name
        self.absences_count = absences_count

    def toDict(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "absences_count": self.absences_count
        }