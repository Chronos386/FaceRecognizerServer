import json


class SendSubject:
    def __init__(self, id_: int, name: str):
        self.id_ = id_
        self.name = name

    def toDict(self) -> dict:
        data = {
            "id": self.id_,
            "name": self.name,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False)
