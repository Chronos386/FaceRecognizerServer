import json
from typing import Optional


class SendAccount:
    def __init__(self, id_: int, is_admin: bool, login: str, name: str, key: str, group_id: Optional[int] = None,
                 group_name: Optional[str] = None, department_id: Optional[int] = None,
                 department_name: Optional[str] = None, institute_id: Optional[int] = None,
                 institute_name: Optional[str] = None):
        self.id: int = id_
        self.is_admin: bool = is_admin
        self.login: str = login
        self.name: str = name
        self.key: str = key
        self.group_id: Optional[int] = group_id  # студент
        self.group_name: Optional[str] = group_name  # студент
        self.department_id: Optional[id] = department_id  # преподаватель
        self.department_name: Optional[str] = department_name  # преподаватель
        self.institute_id: Optional[int] = institute_id  # студент, преподаватель
        self.institute_name: Optional[str] = institute_name  # студент, преподаватель

    def __toDict(self) -> dict:
        data = {
            "id": self.id,
            "hash": self.key,
            "is_admin": self.is_admin,
            "login": self.login,
            "name": self.name
        }
        if self.group_name is not None:
            data["group_id"] = self.group_id
            data["group_name"] = self.group_name
        if self.department_name is not None:
            data["department_id"] = self.department_id
            data["department_name"] = self.department_name
        if self.institute_name is not None:
            data["institute_id"] = self.institute_id
            data["institute_name"] = self.institute_name
        return data

    def toJson(self) -> str:
        return json.dumps(self.__toDict(), ensure_ascii=False)
