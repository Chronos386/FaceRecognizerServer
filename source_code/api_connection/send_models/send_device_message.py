import json


class SendDeviceMessage:
    def __init__(self, schedule_id: int, student_id: int, name: str, group_name: str, subject_name: str):
        self.student_id: int = student_id
        self.schedule_id: int = schedule_id
        self.name: str = name
        self.group_name = group_name
        self.subject_name = subject_name

    def __toDict(self) -> dict:
        data = {
            "student_id": self.student_id,
            "schedule_id": self.schedule_id,
            "name": self.name,
            "group_name": self.group_name,
            "subject_name": self.subject_name,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.__toDict(), ensure_ascii=False)
