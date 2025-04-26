import uuid
import numpy as np
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from typing import Tuple, Optional, Type, List
from datetime import date, timedelta, datetime, time
from source_code.db_connection.db_models.rooms_db import RoomsDB
from source_code.db_connection.db_models.groups_db import GroupsDB
from source_code.db_connection.db_models.hashes_db import HashesDB
from source_code.db_connection.db_models.devices_db import DevicesDB
from source_code.db_connection.db_models.accounts_db import AccountsDB
from source_code.db_connection.db_models.schedule_db import ScheduleDB
from source_code.db_connection.db_models.students_db import StudentsDB
from source_code.db_connection.db_models.subjects_db import SubjectsDB
from source_code.db_connection.db_models.teachers_db import TeachersDB
from source_code.db_connection.db_models.buildings_db import BuildingsDB
from source_code.db_connection.db_models.attendance_db import AttendanceDB
from source_code.db_connection.db_models.institutes_db import InstitutesDB
from source_code.db_connection.db_models.departments_db import DepartmentsDB
from source_code.db_connection.db_models.face_embeddings_db import FaceEmbeddingsDB


class DBClass:
    def __init__(self):
        self.engine = create_engine("postgresql+pg8000://postgres:@localhost/face_recognition_db")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    #  |========================================Свободный ID========================================|
    def __findFirstFreeID(self, table_db) -> int:
        stmt = self.session.query(table_db).order_by(table_db.id.asc()).all()
        count: int = self.session.query(table_db).count()
        mass = []
        for i in range(1, count + 1):
            if i != stmt[i - 1].id:
                mass.append(i)
        if len(mass) != 0:
            count = mass[0]
        else:
            count += 1
        return count

    #  |============================================Хэши============================================|
    def deleteAllHashes(self) -> None:
        old_hashes = self.session.query(HashesDB).all()
        for hash_entry in old_hashes:
            self.session.delete(hash_entry)
        self.session.commit()
        return

    def deleteOldHashes(self) -> None:
        cutoff_date = date.today() - timedelta(days=30)
        old_hashes = self.session.query(HashesDB).filter(HashesDB.date < cutoff_date).all()
        for hash_entry in old_hashes:
            self.session.delete(hash_entry)
        self.session.commit()
        return

    #  |============================================Аккаунт============================================|
    def createAccount(self, email: str, password: str):
        account_db = self.session.query(AccountsDB).filter_by(email=email, password=password).first()
        if account_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(AccountsDB)
        acc_new = AccountsDB(id=new_id, email=email, password=password, admin=False)
        self.session.add(acc_new)
        self.session.commit()
        return acc_new

    def deleteAccount(self, acc_id: int) -> None:
        account_db = self.session.query(AccountsDB).filter_by(id=acc_id).first()
        if account_db is None:
            return
        self.session.delete(account_db)
        self.session.commit()
        return

    def loginByPassword(self, email: str, password: str) -> Optional[Tuple[Type[AccountsDB], str]]:
        account_db = self.session.query(AccountsDB).filter_by(email=email, password=password).first()
        if account_db is None:
            return None
        existing_hashes = (self.session.query(HashesDB).filter_by(acc_id=account_db.id)
                           .order_by(HashesDB.date.asc()).all())
        if len(existing_hashes) >= 5:
            oldest_hash = existing_hashes[0]
            self.session.delete(oldest_hash)
            self.session.commit()

        key: str = uuid.uuid4().hex[:30].upper()
        new_id: int = self.__findFirstFreeID(HashesDB)
        current_date = date.today()
        hash_new = HashesDB(id=new_id, hash=key, date=current_date, acc_id=account_db.id)
        self.session.add(hash_new)
        self.session.commit()
        return account_db, key

    def getAccByHash(self, hash_key: str) -> Optional[AccountsDB]:
        hash_db: Optional[HashesDB] = self.session.query(HashesDB).filter_by(hash=hash_key).first()
        if hash_db is None:
            return None
        account_db: Optional[AccountsDB] = self.session.query(AccountsDB).filter_by(id=hash_db.acc_id).first()
        return account_db

    def logoutByHash(self, hash_key: str) -> bool:
        hash_db: Optional[HashesDB] = self.session.query(HashesDB).filter_by(hash=hash_key).first()
        if hash_db is None:
            return False
        self.session.delete(hash_db)
        self.session.commit()
        return True

    #  |============================================Студент============================================|
    def getStudentByID(self, student_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = self.session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return None
        return student_db

    def getStudentByAccID(self, acc_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = self.session.query(StudentsDB).filter_by(acc_id=acc_id).first()
        if student_db is None:
            return None
        return student_db

    def getAllStudentsByGroup(self, group_id: int) -> Optional[List[Type[StudentsDB]]]:
        student_db: List[Type[StudentsDB]] = self.session.query(StudentsDB).filter_by(group_id=group_id).all()
        if student_db is None:
            return None
        return student_db

    def getStudentsWithoutAttendance(self, schedule_id: int) -> Optional[List[StudentsDB]]:
        students_without_attendance = self.session.query(StudentsDB).join(GroupsDB).join(ScheduleDB).filter(
            ScheduleDB.id == schedule_id
        ).outerjoin(AttendanceDB, (AttendanceDB.schedule_id == schedule_id) &
                    (AttendanceDB.student_id == StudentsDB.id)).filter(AttendanceDB.id == None).all()
        return students_without_attendance if students_without_attendance else None

    def createStudent(self, name: str, acc_id: int, group_id: int):
        student_db: Optional[StudentsDB] = self.session.query(StudentsDB).filter_by(acc_id=acc_id).first()
        if student_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(StudentsDB)
        student_new = StudentsDB(id=new_id, name=name, acc_id=acc_id, group_id=group_id)
        self.session.add(student_new)
        self.session.commit()
        return student_new

    def updateStudent(self, student_id: int, name: str, group_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = self.session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return None
        student_db.name = name
        student_db.group_id = group_id
        self.session.commit()
        return student_db

    def deleteStudent(self, student_id: int) -> bool:
        student_db: Optional[StudentsDB] = self.session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return False
        embeddings: List[Type[FaceEmbeddingsDB]] = self.session.query(FaceEmbeddingsDB).filter_by(student_id=student_id).all()
        for embedding in embeddings:
            self.session.delete(embedding)
        attendance: List[Type[AttendanceDB]] = self.session.query(AttendanceDB).filter_by(student_id=student_id).all()
        for attend in attendance:
            self.session.delete(attend)
        self.session.commit()
        self.session.delete(student_db)
        self.session.commit()
        account: Optional[AccountsDB] = self.session.query(AccountsDB).filter_by(id=student_db.acc_id).first()
        hashes: List[Type[HashesDB]] = self.session.query(HashesDB).filter_by(acc_id=account.id).all()
        for hash_ in hashes:
            self.session.delete(hash_)
        self.session.commit()
        self.session.delete(account)
        self.session.commit()
        return True

    #  |==========================================Эмбиддинги===========================================|
    def getAllEmbeddings(self):
        embeddings: List[Type[FaceEmbeddingsDB]] = self.session.query(FaceEmbeddingsDB).all()
        return embeddings

    def createEmbedding(self, embedding: np.ndarray, student_id: int, path_photo: str):
        embedding_list = embedding.tolist()
        new_id: int = self.__findFirstFreeID(FaceEmbeddingsDB)
        embedding_new = FaceEmbeddingsDB(id=new_id, embedding=embedding_list, student_id=student_id,
                                         path_photo=path_photo)
        self.session.add(embedding_new)
        self.session.commit()
        return embedding_new

    #  |============================================Учитель============================================|
    def getTeacherByID(self, teacher_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = self.session.query(TeachersDB).filter_by(id=teacher_id).first()
        if teacher_db is None:
            return None
        return teacher_db

    def getTeacherByAccID(self, acc_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = self.session.query(TeachersDB).filter_by(acc_id=acc_id).first()
        if teacher_db is None:
            return None
        return teacher_db

    def getAllTeachersByDepartment(self, department_id: int):
        teachers_db: List[Type[TeachersDB]] = (self.session.query(TeachersDB).filter_by(department_id=department_id).all())
        if teachers_db is None:
            return None
        return teachers_db

    def createTeacher(self, name: str, acc_id: int, department_id: int):
        teacher_db: Optional[TeachersDB] = self.session.query(TeachersDB).filter_by(acc_id=acc_id).first()
        if teacher_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(TeachersDB)
        teacher_new = TeachersDB(id=new_id, name=name, acc_id=acc_id, department_id=department_id)
        self.session.add(teacher_new)
        self.session.commit()
        return teacher_new

    def updateTeacher(self, id_teacher: int, name: str, department_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = self.session.query(TeachersDB).filter_by(id=id_teacher).first()
        if teacher_db is None:
            return None
        teacher_db.name = name
        teacher_db.department_id = department_id
        self.session.commit()
        return teacher_db

    def deleteTeacher(self, id_teacher: int) -> bool:
        teacher_db: Optional[TeachersDB] = self.session.query(TeachersDB).filter_by(id=id_teacher).first()
        if teacher_db is None:
            return False

        schedules: List[Type[ScheduleDB]] = self.session.query(ScheduleDB).filter_by(teacher_id=teacher_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        self.session.commit()

        self.session.delete(teacher_db)
        self.session.commit()
        account: Optional[AccountsDB] = self.session.query(AccountsDB).filter_by(id=teacher_db.acc_id).first()
        hashes: List[Type[HashesDB]] = self.session.query(HashesDB).filter_by(acc_id=account.id).all()
        for hash_ in hashes:
            self.session.delete(hash_)
        self.session.commit()
        self.session.delete(account)
        self.session.commit()
        return True

    #  |============================================Группы============================================|
    def getGroupByID(self, group_id: int) -> Optional[GroupsDB]:
        group_db: Optional[GroupsDB] = self.session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return None
        return group_db

    def getAllGroups(self):
        groups_db: List[Type[GroupsDB]] = (self.session.query(GroupsDB).all())
        if groups_db is None:
            return None
        return groups_db

    def getAllGroupsByInstitute(self, institute_id: int):
        groups_db: List[Type[GroupsDB]] = (self.session.query(GroupsDB).filter_by(institute_id=institute_id).all())
        if groups_db is None:
            return None
        return groups_db

    def createGroup(self, id_institute: int, name: str):
        group_db: Optional[GroupsDB] = self.session.query(GroupsDB).filter_by(institute_id=id_institute, name=name).first()
        if group_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(GroupsDB)
        group_new = GroupsDB(id=new_id, name=name, institute_id=id_institute)
        self.session.add(group_new)
        self.session.commit()
        return group_new

    def updateGroup(self, group_id: int, name: str, id_institute: int) -> Optional[GroupsDB]:
        group_db: Optional[GroupsDB] = self.session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return None
        group_db.name = name
        group_db.institute_id = id_institute
        self.session.commit()
        return group_db

    def deleteGroup(self, group_id: int) -> bool:
        group_db: Optional[GroupsDB] = self.session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return False

        students = self.getAllStudentsByGroup(group_db.id)
        for student in students:
            self.deleteStudent(student.id)
        self.session.commit()
        schedules: List[Type[ScheduleDB]] = self.session.query(ScheduleDB).filter_by(group_id=group_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        self.session.commit()

        self.session.delete(group_db)
        self.session.commit()
        return True

    #  |============================================Кафедра============================================|
    def getDepartmentByID(self, department_id: int) -> Optional[DepartmentsDB]:
        department_db: Optional[DepartmentsDB] = self.session.query(DepartmentsDB).filter_by(id=department_id).first()
        if department_db is None:
            return None
        return department_db

    def getAllDepartmentsByInstitute(self, id_institute: int) -> Optional[List[Type[DepartmentsDB]]]:
        departments_db: List[Type[DepartmentsDB]] = (self.session.query(DepartmentsDB).filter_by(institute_id=id_institute).all())
        if departments_db is None:
            return None
        return departments_db

    def createDepartment(self, id_institute: int, name: str) -> Optional[DepartmentsDB]:
        department_db = self.session.query(DepartmentsDB).filter_by(institute_id=id_institute, name=name).first()
        if department_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(DepartmentsDB)
        department_new = DepartmentsDB(id=new_id, name=name, institute_id=id_institute)
        self.session.add(department_new)
        self.session.commit()
        return department_new

    def updateDepartment(self, id_department: int, id_institute: int, name: str) -> Optional[DepartmentsDB]:
        department_db: Optional[DepartmentsDB] = self.session.query(DepartmentsDB).filter_by(id=id_department).first()
        if department_db is None:
            return None
        department_db.name = name
        department_db.institute_id = id_institute
        self.session.commit()
        return department_db

    def deleteDepartment(self, id_department: int) -> bool:
        department_db: Optional[DepartmentsDB] = self.session.query(DepartmentsDB).filter_by(id=id_department).first()
        if department_db is None:
            return False
        teachers = self.getAllTeachersByDepartment(department_db.id)
        for teacher in teachers:
            self.deleteTeacher(teacher.id)
        self.session.commit()
        self.session.delete(department_db)
        self.session.commit()
        return True

    #  |============================================Институт============================================|
    def getInstituteByID(self, institute_id: int) -> Optional[InstitutesDB]:
        institute_db: Optional[InstitutesDB] = self.session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return None
        return institute_db

    def getAllInstitutes(self) -> Optional[List[Type[InstitutesDB]]]:
        institutes_db: List[Type[InstitutesDB]] = self.session.query(InstitutesDB).all()
        if institutes_db is None:
            return None
        return institutes_db

    def createInstitute(self, name: str) -> Optional[InstitutesDB]:
        institute_db = self.session.query(InstitutesDB).filter_by(name=name).first()
        if institute_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(InstitutesDB)
        institute_new = InstitutesDB(id=new_id, name=name)
        self.session.add(institute_new)
        self.session.commit()
        return institute_new

    def updateInstitute(self, institute_id: int, name: str) -> Optional[InstitutesDB]:
        institute_db: Optional[InstitutesDB] = self.session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return None
        institute_db.name = name
        self.session.commit()
        return institute_db

    def deleteInstitute(self, institute_id: int) -> bool:
        institute_db: Optional[InstitutesDB] = self.session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return False
        groups = self.getAllGroupsByInstitute(institute_db.id)
        for group in groups:
            self.deleteGroup(group.id)
        departments = self.getAllDepartmentsByInstitute(institute_db.id)
        for department in departments:
            self.deleteDepartment(department.id)
        self.session.delete(institute_db)
        self.session.commit()
        return True

    #  |============================================Предмет============================================|
    def getSubjectByID(self, subject_id: int) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = self.session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return None
        return subject_db

    def getAllSubjects(self) -> Optional[List[Type[SubjectsDB]]]:
        subject_db: List[Type[SubjectsDB]] = self.session.query(SubjectsDB).all()
        if subject_db is None:
            return None
        return subject_db

    def createSubject(self, name: str) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = self.session.query(SubjectsDB).filter_by(name=name).first()
        if subject_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(SubjectsDB)
        subject_new = SubjectsDB(id=new_id, name=name)
        self.session.add(subject_new)
        self.session.commit()
        return subject_new

    def updateSubject(self, subject_id: int, name: str) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = self.session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return None
        subject_db.name = name
        self.session.commit()
        return subject_db

    def deleteSubject(self, subject_id: int) -> bool:
        subject_db: Optional[SubjectsDB] = self.session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return False
        schedules: List[Type[ScheduleDB]] = self.session.query(ScheduleDB).filter_by(subject_id=subject_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        self.session.commit()
        self.session.delete(subject_db)
        self.session.commit()
        return True

    #  |============================================Корпус============================================|
    def getBuildingByID(self, building_id: int) -> Optional[BuildingsDB]:
        building_db: Optional[BuildingsDB] = self.session.query(BuildingsDB).filter_by(id=building_id).first()
        if building_db is None:
            return None
        return building_db

    def getAllBuildings(self):
        buildings_db: List[Type[BuildingsDB]] = self.session.query(BuildingsDB).all()
        if buildings_db is None:
            return None
        return buildings_db

    def createBuilding(self, name: str, address: str) -> Optional[BuildingsDB]:
        building: Optional[BuildingsDB] = self.session.query(BuildingsDB).filter_by(name=name, address=address).first()
        if building is not None:
            return None

        new_id: int = self.__findFirstFreeID(BuildingsDB)
        building_new = BuildingsDB(id=new_id, name=name, address=address)
        self.session.add(building_new)
        self.session.commit()
        return building_new

    def updateBuilding(self, building_id: int, name: str, address: str) -> Optional[BuildingsDB]:
        building: Optional[BuildingsDB] = self.session.query(BuildingsDB).filter_by(id=building_id).first()
        if building is None:
            return None
        building.name = name
        building.address = address
        self.session.commit()
        return building

    def deleteBuilding(self, building_id: int) -> bool:
        building: Optional[BuildingsDB] = self.session.query(BuildingsDB).filter_by(id=building_id).first()
        if building is None:
            return False
        rooms: List[Type[RoomsDB]] = self.session.query(RoomsDB).filter_by(building_id=building_id).all()
        for room in rooms:
            self.deleteRoom(room.id)
        self.session.commit()
        self.session.delete(building)
        self.session.commit()
        return True

    #  |============================================Кабинет============================================|
    def getRoomByID(self, room_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = self.session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return None
        return room_db

    def getRoomByDeviceID(self, device_id: int) -> Optional[RoomsDB]:
        device_db: Optional[DevicesDB] = self.session.query(DevicesDB).filter_by(id=device_id).first()
        if device_db is None:
            return None
        room_db: Optional[RoomsDB] = self.session.query(RoomsDB).filter_by(id=device_db.room_id).first()
        if room_db is None:
            return None
        return room_db

    def getAllRoomsByBuilding(self, building_id: int) -> Optional[List[Type[RoomsDB]]]:
        rooms: List[Type[RoomsDB]] = self.session.query(RoomsDB).filter_by(building_id=building_id).all()
        if rooms is None:
            return None
        return rooms

    def createRoom(self, number: str, building_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = self.session.query(RoomsDB).filter_by(number=number, building_id=building_id).first()
        if room_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(RoomsDB)
        room_new = RoomsDB(id=new_id, number=number, building_id=building_id)
        self.session.add(room_new)
        self.session.commit()
        return room_new

    def updateRoom(self, room_id: int, number: str, building_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = self.session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return None
        room_db.number = number
        room_db.building_id = building_id
        self.session.commit()
        return room_db

    def deleteRoom(self, room_id: int) -> bool:
        room_db: Optional[RoomsDB] = self.session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return False
        schedules: List[Type[ScheduleDB]] = self.session.query(ScheduleDB).filter_by(room_id=room_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        devices: List[Type[DevicesDB]] = self.session.query(DevicesDB).filter_by(room_id=room_db.id).all()
        for device in devices:
            self.session.delete(device)
        self.session.commit()
        self.session.delete(room_db)
        self.session.commit()
        return True

    #  |==============================================Девайс==============================================|
    def checkDeviceByRoomID(self, room_id: int) -> Optional[int]:
        device_db: Optional[DevicesDB] = self.session.query(DevicesDB).filter_by(room_id=room_id).first()
        if device_db is None:
            return None
        return device_db.id

    def createDevice(self, room_id: int) -> Optional[DevicesDB]:
        device: Optional[DevicesDB] = self.session.query(DevicesDB).filter_by(room_id=room_id).first()
        if device is not None:
            return None

        new_id: int = self.__findFirstFreeID(DevicesDB)
        device = DevicesDB(id=new_id, room_id=room_id)
        self.session.add(device)
        self.session.commit()
        return device

    def deleteDevice(self, device_id: int) -> bool:
        device: Optional[DevicesDB] = self.session.query(DevicesDB).filter_by(id=device_id).first()
        if device is None:
            return False
        self.session.delete(device)
        self.session.commit()
        return True

    #  |============================================Расписание============================================|
    def getScheduleByID(self, schedule_id: int) -> Optional[ScheduleDB]:
        schedule_db: Optional[ScheduleDB] = self.session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule_db is None:
            return None
        return schedule_db

    def getScheduleForGroup(self, group_id: int, week_start: date, week_end: date) -> Optional[List[Type[ScheduleDB]]]:
        schedule_records = self.session.query(ScheduleDB).filter(
            ScheduleDB.date >= week_start,
            ScheduleDB.date <= week_end,
            ScheduleDB.group_id == group_id
        ).all()
        if schedule_records is None:
            return None
        return schedule_records

    def getScheduleForTeacher(self, teacher_id: int, week_start: date, week_end: date) -> Optional[List[Type[ScheduleDB]]]:
        schedule_records = self.session.query(ScheduleDB).filter(
            ScheduleDB.date >= week_start,
            ScheduleDB.date <= week_end,
            ScheduleDB.teacher_id == teacher_id
        ).all()
        if schedule_records is None:
            return None
        return schedule_records

    def getScheduleForAttendance(self, group_id: int, room_id: int, current_datetime: datetime) -> Optional[ScheduleDB]:
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        time_threshold = (datetime.combine(current_date, current_time) + timedelta(minutes=10)).time()
        schedule_record = self.session.query(ScheduleDB).filter(
            ScheduleDB.group_id == group_id,
            ScheduleDB.room_id == room_id,
            ScheduleDB.date == current_date,
            ScheduleDB.time_start < time_threshold,
            ScheduleDB.time_end >= time_threshold
        ).first()
        return schedule_record

    def getMissedSchedules(self, current_datetime: datetime) -> Optional[List[Type[ScheduleDB]]]:
        time_threshold = current_datetime - timedelta(hours=3)
        missed_schedules = self.session.query(ScheduleDB).filter(
            (ScheduleDB.date < current_datetime.date()) |
            ((ScheduleDB.date == current_datetime.date()) & (ScheduleDB.time_end <= current_datetime.time())),
            (ScheduleDB.date > time_threshold.date()) |
            ((ScheduleDB.date == time_threshold.date()) & (ScheduleDB.time_end >= time_threshold.time())),
        ).all()
        return missed_schedules if missed_schedules else None

    def createSchedule(self, date_schedule: date, time_start: time, time_end: time, group_id: int, subject_id: int,
                       teacher_id: int, room_id: int) -> Optional[ScheduleDB]:
        schedule: Optional[ScheduleDB] = self.session.query(ScheduleDB).filter_by(date=date_schedule,
                                                                                  time_start=time_start,
                                                                                  time_end=time_end, group_id=group_id,
                                                                                  subject_id=subject_id,
                                                                                  teacher_id=teacher_id,
                                                                                  room_id=room_id).first()
        if schedule is not None:
            return None

        new_id: int = self.__findFirstFreeID(ScheduleDB)
        schedule: ScheduleDB = ScheduleDB(id=new_id, date=date_schedule, time_start=time_start, time_end=time_end,
                                          group_id=group_id, subject_id=subject_id, teacher_id=teacher_id,
                                          room_id=room_id)
        self.session.add(schedule)
        self.session.commit()
        return schedule

    def updateSchedule(self, schedule_id: int, date_schedule: date, time_start: time, time_end: time, group_id: int,
                       subject_id: int, teacher_id: int, room_id: int) -> Optional[ScheduleDB]:
        schedule: Optional[ScheduleDB] = self.session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule is None:
            return None
        schedule.date = date_schedule
        schedule.time_start = time_start
        schedule.time_end = time_end
        schedule.group_id = group_id
        schedule.subject_id = subject_id
        schedule.teacher_id = teacher_id
        schedule.room_id = room_id
        self.session.commit()
        return schedule

    def deleteSchedule(self, schedule_id: int) -> bool:
        schedule: Optional[ScheduleDB] = self.session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule is None:
            return False
        attendances: List[Type[AttendanceDB]] = self.session.query(AttendanceDB).filter_by(schedule_id=schedule.id).all()
        for attendance in attendances:
            self.session.delete(attendance)
        self.session.commit()
        self.session.delete(schedule)
        self.session.commit()
        return True

    #  |============================================Посещаемость============================================|
    def markAttendance(self, student_id: int, schedule_id: int, status: bool):
        existing_record = self.session.query(AttendanceDB).filter_by(
            student_id=student_id,
            schedule_id=schedule_id
        ).first()
        if existing_record:
            existing_record.status = status
        else:
            new_id: int = self.__findFirstFreeID(AttendanceDB)
            new_attendance = AttendanceDB(
                id=new_id,
                status=status,
                student_id=student_id,
                schedule_id=schedule_id
            )
            self.session.add(new_attendance)
        self.session.commit()
        return

    def deleteWrongAttendance(self, student_id: int, schedule_id) -> bool:
        existing_record = self.session.query(AttendanceDB).filter_by(
            student_id=student_id,
            schedule_id=schedule_id
        ).first()
        if existing_record is None:
            return False
        self.session.delete(existing_record)
        self.session.commit()
        return True

    def getAttendanceByScheduleId(self, schedule_id: int) -> Optional[List[Type[AttendanceDB]]]:
        attendance_db: List[Type[AttendanceDB]] = self.session.query(AttendanceDB).filter_by(schedule_id=schedule_id).all()
        if attendance_db is None:
            return None
        return attendance_db

    def getStudentAttendanceByScheduleId(self, student_id: int, schedule_id: int) -> Optional[AttendanceDB]:
        attendance_db: Optional[AttendanceDB] = self.session.query(AttendanceDB).filter_by(schedule_id=schedule_id,
                                                                                           student_id=student_id).first()
        if attendance_db is None:
            return None
        return attendance_db
