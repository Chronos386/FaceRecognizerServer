class SendStudents:
    def __init__(self, id_: int, name: str, acc_id: int, group: str, group_id: int):
        self.id: int = id_
        self.name: str = name
        self.group: str = group
        self.group_id: int = group_id
        self.acc_id: int = acc_id

    def toDict(self) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "group_id": self.group_id,
            "acc_id": self.acc_id,
        }
        return data
