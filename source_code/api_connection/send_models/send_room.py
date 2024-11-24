import json
from typing import Optional


class SendRoom:
    def __init__(self, id_: int, number: str, building_id: int, device_id: Optional[int] = None):
        self.id_: int = id_
        self.number: str = number
        self.device_id: Optional[int] = device_id
        self.building_id: int = building_id

    def toDict(self) -> dict:
        data = {
            "id": self.id_,
            "number": self.number,
            "device_id": self.device_id,
            "building_id": self.building_id,
        }
        return data

    def toJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False)
