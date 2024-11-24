import json


class SendDepartments:
    def __init__(self, id_: int, name: str, institute: str, institute_id: int):
        self.id_ = id_
        self.name = name
        self.institute = institute
        self.institute_id = institute_id

    def toDict(self) -> dict:
        data = {
            "id": self.id_,
            "name": self.name,
            "institute_id": self.institute_id,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False)
