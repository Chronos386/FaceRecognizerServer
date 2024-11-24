import json


class SendBuildings(object):
    def __init__(self, id_: int, name: str, address: str):
        self.id_ = id_
        self.name = name
        self.address = address

    def toDict(self) -> dict:
        data = {
            "id": self.id_,
            "name": self.name,
            "address": self.address,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False)