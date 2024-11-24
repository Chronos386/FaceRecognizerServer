import json


class SendTeacher:
    def __init__(self, id_: int, name: str, acc_id: int, department: str, department_id: int):
        self.id: int = id_
        self.name: str = name
        self.acc_id: int = acc_id
        self.department: str = department
        self.department_id: int = department_id

    def toDict(self) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "acc_id": self.acc_id,
            "department": self.department,
            "department_id": self.department_id,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False)
