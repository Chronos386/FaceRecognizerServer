import uuid
import numpy as np
from sqlalchemy import *
from functools import wraps
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


def with_session(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self.getSession() as session:
            return method(self, session, *args, **kwargs)

    return wrapper


class DBClass:
    def __init__(self):
        self.engine = create_engine("postgresql+pg8000://postgres:Chronos386@localhost/face_recognition_db")
        self.Session = sessionmaker(bind=self.engine)

    #  |========================================Доп. функции========================================|
    def getSession(self):
        session = self.Session()
        return session

    @staticmethod
    def __findFirstFreeID(session, table_db) -> int:
        stmt = session.query(table_db).order_by(table_db.id.asc()).all()
        count: int = session.query(table_db).count()
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
    @with_session
    def deleteAllHashes(self, session) -> None:
        old_hashes = session.query(HashesDB).all()
        for hash_entry in old_hashes:
            session.delete(hash_entry)
        session.commit()
        return

    @with_session
    def deleteOldHashes(self, session) -> None:
        cutoff_date = date.today() - timedelta(days=30)
        old_hashes = session.query(HashesDB).filter(HashesDB.date < cutoff_date).all()
        for hash_entry in old_hashes:
            session.delete(hash_entry)
        session.commit()
        return

    #  |============================================Аккаунт============================================|
    @with_session
    def createAccount(self, session, email: str, password: str):
        account_db = session.query(AccountsDB).filter_by(email=email, password=password).first()
        if account_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, AccountsDB)
        acc_new = AccountsDB(id=new_id, email=email, password=password, admin=False)
        session.add(acc_new)
        session.commit()
        return acc_new

    @with_session
    def deleteAccount(self, session, acc_id: int) -> None:
        account_db = session.query(AccountsDB).filter_by(id=acc_id).first()
        if account_db is None:
            return
        session.delete(account_db)
        session.commit()
        return

    @with_session
    def loginByPassword(self, session, email: str, password: str) -> Optional[Tuple[Type[AccountsDB], str]]:
        account_db = session.query(AccountsDB).filter_by(email=email, password=password).first()
        if account_db is None:
            return None
        existing_hashes = (session.query(HashesDB).filter_by(acc_id=account_db.id)
                           .order_by(HashesDB.date.asc()).all())
        if len(existing_hashes) >= 5:
            oldest_hash = existing_hashes[0]
            session.delete(oldest_hash)
            session.commit()

        key: str = uuid.uuid4().hex[:30].upper()
        new_id: int = self.__findFirstFreeID(session, HashesDB)
        current_date = date.today()
        hash_new = HashesDB(id=new_id, hash=key, date=current_date, acc_id=account_db.id)
        session.add(hash_new)
        session.commit()
        return account_db, key

    @with_session
    def getAccByHash(self, session, hash_key: str) -> Optional[AccountsDB]:
        hash_db: Optional[HashesDB] = session.query(HashesDB).filter_by(hash=hash_key).first()
        if hash_db is None:
            return None
        account_db: Optional[AccountsDB] = session.query(AccountsDB).filter_by(id=hash_db.acc_id).first()
        return account_db

    @with_session
    def logoutByHash(self, session, hash_key: str) -> bool:
        hash_db: Optional[HashesDB] = session.query(HashesDB).filter_by(hash=hash_key).first()
        if hash_db is None:
            return False
        session.delete(hash_db)
        session.commit()
        return True

    #  |============================================Студент============================================|
    @with_session
    def getStudentByID(self, session, student_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return None
        return student_db

    @with_session
    def getStudentByAccID(self, session, acc_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = session.query(StudentsDB).filter_by(acc_id=acc_id).first()
        if student_db is None:
            return None
        return student_db

    @with_session
    def getAllStudentsByGroup(self, session, group_id: int) -> Optional[List[Type[StudentsDB]]]:
        student_db: List[Type[StudentsDB]] = session.query(StudentsDB).filter_by(group_id=group_id).all()
        if student_db is None:
            return None
        return student_db

    @with_session
    def getStudentsWithoutAttendance(self, session, schedule_id: int) -> Optional[List[StudentsDB]]:
        students_without_attendance = session.query(StudentsDB).join(GroupsDB).join(ScheduleDB).filter(
            ScheduleDB.id == schedule_id
        ).outerjoin(AttendanceDB, (AttendanceDB.schedule_id == schedule_id) &
                    (AttendanceDB.student_id == StudentsDB.id)).filter(AttendanceDB.id == None).all()
        return students_without_attendance if students_without_attendance else None

    @with_session
    def createStudent(self, session, name: str, acc_id: int, group_id: int):
        student_db: Optional[StudentsDB] = session.query(StudentsDB).filter_by(acc_id=acc_id).first()
        if student_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, StudentsDB)
        student_new = StudentsDB(id=new_id, name=name, acc_id=acc_id, group_id=group_id)
        session.add(student_new)
        session.commit()
        return student_new

    @with_session
    def updateStudent(self, session, student_id: int, name: str, group_id: int) -> Optional[StudentsDB]:
        student_db: Optional[StudentsDB] = session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return None
        student_db.name = name
        student_db.group_id = group_id
        session.commit()
        return student_db

    @with_session
    def deleteStudent(self, session, student_id: int) -> bool:
        student_db: Optional[StudentsDB] = session.query(StudentsDB).filter_by(id=student_id).first()
        if student_db is None:
            return False
        embeddings: List[Type[FaceEmbeddingsDB]] = session.query(FaceEmbeddingsDB).filter_by(
            student_id=student_id).all()
        for embedding in embeddings:
            session.delete(embedding)
        session.commit()
        session.delete(student_db)
        session.commit()
        account: Optional[AccountsDB] = session.query(AccountsDB).filter_by(id=student_db.acc_id).first()
        session.delete(account)
        session.commit()
        return True

    #  |==========================================Эмбиддинги===========================================|
    @with_session
    def getAllEmbeddings(self, session):
        embeddings: List[Type[FaceEmbeddingsDB]] = session.query(FaceEmbeddingsDB).all()
        return embeddings

    @with_session
    def createEmbedding(self, session, embedding: np.ndarray, student_id: int, path_photo: str):
        embedding_list = embedding.tolist()
        new_id: int = self.__findFirstFreeID(session, FaceEmbeddingsDB)
        embedding_new = FaceEmbeddingsDB(id=new_id, embedding=embedding_list, student_id=student_id,
                                         path_photo=path_photo)
        session.add(embedding_new)
        session.commit()
        return embedding_new

    #  |============================================Учитель============================================|
    @with_session
    def getTeacherByID(self, session, teacher_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = session.query(TeachersDB).filter_by(id=teacher_id).first()
        if teacher_db is None:
            return None
        return teacher_db

    @with_session
    def getTeacherByAccID(self, session, acc_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = session.query(TeachersDB).filter_by(acc_id=acc_id).first()
        if teacher_db is None:
            return None
        return teacher_db

    @with_session
    def getAllTeachersByDepartment(self, session, department_id: int):
        teachers_db: List[Type[TeachersDB]] = (
            session.query(TeachersDB).filter_by(department_id=department_id).all())
        if teachers_db is None:
            return None
        return teachers_db

    @with_session
    def createTeacher(self, session, name: str, acc_id: int, department_id: int):
        teacher_db: Optional[TeachersDB] = session.query(TeachersDB).filter_by(acc_id=acc_id).first()
        if teacher_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, TeachersDB)
        teacher_new = TeachersDB(id=new_id, name=name, acc_id=acc_id, department_id=department_id)
        session.add(teacher_new)
        session.commit()
        return teacher_new

    @with_session
    def updateTeacher(self, session, id_teacher: int, name: str, department_id: int) -> Optional[TeachersDB]:
        teacher_db: Optional[TeachersDB] = session.query(TeachersDB).filter_by(id=id_teacher).first()
        if teacher_db is None:
            return None
        teacher_db.name = name
        teacher_db.department_id = department_id
        session.commit()
        return teacher_db

    @with_session
    def deleteTeacher(self, session, id_teacher: int) -> bool:
        teacher_db: Optional[TeachersDB] = session.query(TeachersDB).filter_by(id=id_teacher).first()
        if teacher_db is None:
            return False

        schedules: List[Type[ScheduleDB]] = session.query(ScheduleDB).filter_by(teacher_id=teacher_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        session.commit()

        session.delete(teacher_db)
        session.commit()
        account: Optional[AccountsDB] = session.query(AccountsDB).filter_by(id=teacher_db.acc_id).first()
        session.delete(account)
        session.commit()
        return True

    #  |============================================Группы============================================|
    @with_session
    def getGroupByID(self, session, group_id: int) -> Optional[GroupsDB]:
        group_db: Optional[GroupsDB] = session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return None
        return group_db

    @with_session
    def getAllGroupsByInstitute(self, session, institute_id: int):
        groups_db: List[Type[GroupsDB]] = (session.query(GroupsDB).filter_by(institute_id=institute_id).all())
        if groups_db is None:
            return None
        return groups_db

    @with_session
    def createGroup(self, session, id_institute: int, name: str):
        group_db: Optional[GroupsDB] = session.query(GroupsDB).filter_by(institute_id=id_institute, name=name).first()
        if group_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, GroupsDB)
        group_new = GroupsDB(id=new_id, name=name, institute_id=id_institute)
        session.add(group_new)
        session.commit()
        return group_new

    @with_session
    def updateGroup(self, session, group_id: int, name: str, id_institute: int) -> Optional[GroupsDB]:
        group_db: Optional[GroupsDB] = session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return None
        group_db.name = name
        group_db.institute_id = id_institute
        session.commit()
        return group_db

    @with_session
    def deleteGroup(self, session, group_id: int) -> bool:
        group_db: Optional[GroupsDB] = session.query(GroupsDB).filter_by(id=group_id).first()
        if group_db is None:
            return False

        students = self.getAllStudentsByGroup(group_db.id)
        for student in students:
            self.deleteStudent(student.id)
        session.commit()
        schedules: List[Type[ScheduleDB]] = session.query(ScheduleDB).filter_by(group_id=group_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        session.commit()

        session.delete(group_db)
        session.commit()
        return True

    #  |============================================Кафедра============================================|
    @with_session
    def getDepartmentByID(self, session, department_id: int) -> Optional[DepartmentsDB]:
        department_db: Optional[DepartmentsDB] = session.query(DepartmentsDB).filter_by(id=department_id).first()
        if department_db is None:
            return None
        return department_db

    @with_session
    def getAllDepartmentsByInstitute(self, session, id_institute: int) -> Optional[List[Type[DepartmentsDB]]]:
        departments_db: List[Type[DepartmentsDB]] = (
            session.query(DepartmentsDB).filter_by(institute_id=id_institute).all())
        if departments_db is None:
            return None
        return departments_db

    @with_session
    def createDepartment(self, session, id_institute: int, name: str) -> Optional[DepartmentsDB]:
        department_db = session.query(DepartmentsDB).filter_by(institute_id=id_institute, name=name).first()
        if department_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, DepartmentsDB)
        department_new = DepartmentsDB(id=new_id, name=name, institute_id=id_institute)
        session.add(department_new)
        session.commit()
        return department_new

    @with_session
    def updateDepartment(self, session, id_department: int, id_institute: int, name: str) -> Optional[DepartmentsDB]:
        department_db: Optional[DepartmentsDB] = session.query(DepartmentsDB).filter_by(id=id_department).first()
        if department_db is None:
            return None
        department_db.name = name
        department_db.institute_id = id_institute
        session.commit()
        return department_db

    @with_session
    def deleteDepartment(self, session, id_department: int) -> bool:
        department_db: Optional[DepartmentsDB] = session.query(DepartmentsDB).filter_by(id=id_department).first()
        if department_db is None:
            return False
        teachers = self.getAllTeachersByDepartment(department_db.id)
        for teacher in teachers:
            self.deleteTeacher(teacher.id)
        session.commit()
        session.delete(department_db)
        session.commit()
        return True

    #  |============================================Институт============================================|
    @with_session
    def getInstituteByID(self, session, institute_id: int) -> Optional[InstitutesDB]:
        institute_db: Optional[InstitutesDB] = session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return None
        return institute_db

    @with_session
    def getAllInstitutes(self, session) -> Optional[List[Type[InstitutesDB]]]:
        institutes_db: List[Type[InstitutesDB]] = session.query(InstitutesDB).all()
        if institutes_db is None:
            return None
        return institutes_db

    @with_session
    def createInstitute(self, session, name: str) -> Optional[InstitutesDB]:
        institute_db = session.query(InstitutesDB).filter_by(name=name).first()
        if institute_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, InstitutesDB)
        institute_new = InstitutesDB(id=new_id, name=name)
        session.add(institute_new)
        session.commit()
        return institute_new

    @with_session
    def updateInstitute(self, session, institute_id: int, name: str) -> Optional[InstitutesDB]:
        institute_db: Optional[InstitutesDB] = session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return None
        institute_db.name = name
        session.commit()
        return institute_db

    @with_session
    def deleteInstitute(self, session, institute_id: int) -> bool:
        institute_db: Optional[InstitutesDB] = session.query(InstitutesDB).filter_by(id=institute_id).first()
        if institute_db is None:
            return False
        groups = self.getAllGroupsByInstitute(institute_db.id)
        for group in groups:
            self.deleteGroup(group.id)
        departments = self.getAllDepartmentsByInstitute(institute_db.id)
        for department in departments:
            self.deleteDepartment(department.id)
        session.delete(institute_db)
        session.commit()
        return True

    #  |============================================Предмет============================================|
    @with_session
    def getSubjectByID(self, session, subject_id: int) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return None
        return subject_db

    @with_session
    def getAllSubjects(self, session) -> Optional[List[Type[SubjectsDB]]]:
        subject_db: List[Type[SubjectsDB]] = session.query(SubjectsDB).all()
        if subject_db is None:
            return None
        return subject_db

    @with_session
    def createSubject(self, session, name: str) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = session.query(SubjectsDB).filter_by(name=name).first()
        if subject_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, SubjectsDB)
        subject_new = SubjectsDB(id=new_id, name=name)
        session.add(subject_new)
        session.commit()
        return subject_new

    @with_session
    def updateSubject(self, session, subject_id: int, name: str) -> Optional[SubjectsDB]:
        subject_db: Optional[SubjectsDB] = session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return None
        subject_db.name = name
        session.commit()
        return subject_db

    @with_session
    def deleteSubject(self, session, subject_id: int) -> bool:
        subject_db: Optional[SubjectsDB] = session.query(SubjectsDB).filter_by(id=subject_id).first()
        if subject_db is None:
            return False
        schedules: List[Type[ScheduleDB]] = session.query(ScheduleDB).filter_by(subject_id=subject_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        session.commit()
        session.delete(subject_db)
        return True

    #  |============================================Корпус============================================|
    @with_session
    def getBuildingByID(self, session, building_id: int) -> Optional[BuildingsDB]:
        building_db: Optional[BuildingsDB] = session.query(BuildingsDB).filter_by(id=building_id).first()
        if building_db is None:
            return None
        return building_db

    @with_session
    def getAllBuildings(self, session):
        buildings_db: List[Type[BuildingsDB]] = session.query(BuildingsDB).all()
        if buildings_db is None:
            return None
        return buildings_db

    @with_session
    def createBuilding(self, session, name: str, address: str) -> Optional[BuildingsDB]:
        building: Optional[BuildingsDB] = session.query(BuildingsDB).filter_by(name=name, address=address).first()
        if building is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, BuildingsDB)
        building_new = BuildingsDB(id=new_id, name=name, address=address)
        session.add(building_new)
        session.commit()
        return building_new

    @with_session
    def updateBuilding(self, session, building_id: int, name: str, address: str) -> Optional[BuildingsDB]:
        building: Optional[BuildingsDB] = session.query(BuildingsDB).filter_by(id=building_id).first()
        if building is None:
            return None
        building.name = name
        building.address = address
        session.commit()
        return building

    @with_session
    def deleteBuilding(self, session, building_id: int) -> bool:
        building: Optional[BuildingsDB] = session.query(BuildingsDB).filter_by(id=building_id).first()
        if building is None:
            return False
        rooms: List[Type[RoomsDB]] = session.query(RoomsDB).filter_by(building_id=building_id).all()
        for room in rooms:
            self.deleteRoom(room.id)
        session.commit()
        session.delete(building)
        session.commit()
        return True

    #  |============================================Кабинет============================================|
    @with_session
    def getRoomByID(self, session, room_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return None
        return room_db

    @with_session
    def getRoomByDeviceID(self, session, device_id: int) -> Optional[RoomsDB]:
        device_db: Optional[DevicesDB] = session.query(DevicesDB).filter_by(id=device_id).first()
        if device_db is None:
            return None
        room_db: Optional[RoomsDB] = session.query(RoomsDB).filter_by(id=device_db.room_id).first()
        if room_db is None:
            return None
        return room_db

    @with_session
    def getAllRoomsByBuilding(self, session, building_id: int) -> Optional[List[Type[RoomsDB]]]:
        rooms: List[Type[RoomsDB]] = session.query(RoomsDB).filter_by(building_id=building_id).all()
        if rooms is None:
            return None
        return rooms

    @with_session
    def createRoom(self, session, number: str, building_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = session.query(RoomsDB).filter_by(number=number, building_id=building_id).first()
        if room_db is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, RoomsDB)
        room_new = RoomsDB(id=new_id, number=number, building_id=building_id)
        session.add(room_new)
        session.commit()
        return room_new

    @with_session
    def updateRoom(self, session, room_id: int, number: str, building_id: int) -> Optional[RoomsDB]:
        room_db: Optional[RoomsDB] = session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return None
        room_db.number = number
        room_db.building_id = building_id
        session.commit()
        return room_db

    @with_session
    def deleteRoom(self, session, room_id: int) -> bool:
        room_db: Optional[RoomsDB] = session.query(RoomsDB).filter_by(id=room_id).first()
        if room_db is None:
            return False
        schedules: List[Type[ScheduleDB]] = session.query(ScheduleDB).filter_by(room_id=room_db.id).all()
        for schedule in schedules:
            self.deleteSchedule(schedule.id)
        devices: List[Type[DevicesDB]] = session.query(DevicesDB).filter_by(room_id=room_db.id).all()
        for device in devices:
            session.delete(device)
        session.commit()
        session.delete(room_db)
        session.commit()
        return True

    #  |==============================================Девайс==============================================|
    @with_session
    def checkDeviceByRoomID(self, session, room_id: int) -> Optional[int]:
        device_db: Optional[DevicesDB] = session.query(DevicesDB).filter_by(room_id=room_id).first()
        if device_db is None:
            return None
        return device_db.id

    @with_session
    def createDevice(self, session, room_id: int) -> Optional[DevicesDB]:
        device: Optional[DevicesDB] = session.query(DevicesDB).filter_by(room_id=room_id).first()
        if device is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, DevicesDB)
        device = DevicesDB(id=new_id, room_id=room_id)
        session.add(device)
        session.commit()
        return device

    @with_session
    def deleteDevice(self, session, device_id: int) -> bool:
        device: Optional[DevicesDB] = session.query(DevicesDB).filter_by(id=device_id).first()
        if device is None:
            return False
        session.delete(device)
        session.commit()
        return True

    #  |============================================Расписание============================================|
    @with_session
    def getScheduleByID(self, session, schedule_id: int) -> Optional[ScheduleDB]:
        schedule_db: Optional[ScheduleDB] = session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule_db is None:
            return None
        return schedule_db

    @with_session
    def getScheduleForGroup(self, session, group_id: int, week_start: date, week_end: date) -> (
            Optional)[List[Type[ScheduleDB]]]:
        schedule_records = session.query(ScheduleDB).filter(
            ScheduleDB.date >= week_start,
            ScheduleDB.date <= week_end,
            ScheduleDB.group_id == group_id
        ).all()
        if schedule_records is None:
            return None
        return schedule_records

    @with_session
    def getScheduleForTeacher(self, session, teacher_id: int, week_start: date,
                              week_end: date) -> Optional[List[Type[ScheduleDB]]]:
        schedule_records = session.query(ScheduleDB).filter(
            ScheduleDB.date >= week_start,
            ScheduleDB.date <= week_end,
            ScheduleDB.teacher_id == teacher_id
        ).all()
        if schedule_records is None:
            return None
        return schedule_records

    @with_session
    def getScheduleForAttendance(self, session, group_id: int, room_id: int, current_datetime: datetime) -> (
            Optional)[ScheduleDB]:
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        time_threshold = (datetime.combine(current_date, current_time) + timedelta(minutes=10)).time()
        schedule_record = session.query(ScheduleDB).filter(
            ScheduleDB.group_id == group_id,
            ScheduleDB.room_id == room_id,
            ScheduleDB.date == current_date,
            ScheduleDB.time_start < time_threshold,
            ScheduleDB.time_end >= time_threshold
        ).first()
        return schedule_record

    @with_session
    def getMissedSchedules(self, session, current_datetime: datetime) -> Optional[List[Type[ScheduleDB]]]:
        time_threshold = current_datetime - timedelta(hours=3)
        missed_schedules = session.query(ScheduleDB).filter(
            (ScheduleDB.date < current_datetime.date()) |
            ((ScheduleDB.date == current_datetime.date()) & (ScheduleDB.time_end <= current_datetime.time())),
            (ScheduleDB.date > time_threshold.date()) |
            ((ScheduleDB.date == time_threshold.date()) & (ScheduleDB.time_end >= time_threshold.time())),
        ).all()
        return missed_schedules if missed_schedules else None

    @with_session
    def createSchedule(self, session, date_schedule: date, time_start: time, time_end: time, group_id: int,
                       subject_id: int, teacher_id: int, room_id: int) -> Optional[ScheduleDB]:
        schedule: Optional[ScheduleDB] = session.query(ScheduleDB).filter_by(date=date_schedule, time_start=time_start,
                                                                             time_end=time_end, group_id=group_id,
                                                                             subject_id=subject_id, room_id=room_id,
                                                                             eacher_id=teacher_id).first()
        if schedule is not None:
            return None

        new_id: int = self.__findFirstFreeID(session, ScheduleDB)
        schedule: ScheduleDB = ScheduleDB(id=new_id, date=date_schedule, time_start=time_start, time_end=time_end,
                                          group_id=group_id, subject_id=subject_id, teacher_id=teacher_id,
                                          room_id=room_id)
        session.add(schedule)
        session.commit()
        return schedule

    @with_session
    def updateSchedule(self, session, schedule_id: int, date_schedule: date, time_start: time, time_end: time,
                       group_id: int, subject_id: int, teacher_id: int, room_id: int) -> Optional[ScheduleDB]:
        schedule: Optional[ScheduleDB] = session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule is None:
            return None
        schedule.date = date_schedule
        schedule.time_start = time_start
        schedule.time_end = time_end
        schedule.group_id = group_id
        schedule.subject_id = subject_id
        schedule.teacher_id = teacher_id
        schedule.room_id = room_id
        session.commit()
        return schedule

    @with_session
    def deleteSchedule(self, session, schedule_id: int) -> bool:
        schedule: Optional[ScheduleDB] = session.query(ScheduleDB).filter_by(id=schedule_id).first()
        if schedule is None:
            return False
        attendances: List[Type[AttendanceDB]] = session.query(AttendanceDB).filter_by(
            schedule_id=schedule.id).all()
        for attendance in attendances:
            session.delete(attendance)
        session.commit()
        session.delete(schedule)
        session.commit()
        return True

    #  |============================================Посещаемость============================================|
    @with_session
    def markAttendance(self, session, student_id: int, schedule_id: int, status: bool):
        existing_record = session.query(AttendanceDB).filter_by(
            student_id=student_id,
            schedule_id=schedule_id
        ).first()
        if existing_record:
            existing_record.status = status
        else:
            new_id: int = self.__findFirstFreeID(session, AttendanceDB)
            new_attendance = AttendanceDB(
                id=new_id,
                status=status,
                student_id=student_id,
                schedule_id=schedule_id
            )
            session.add(new_attendance)
        session.commit()
        return

    @with_session
    def deleteWrongAttendance(self, session, student_id: int, schedule_id) -> bool:
        existing_record = session.query(AttendanceDB).filter_by(
            student_id=student_id,
            schedule_id=schedule_id
        ).first()
        if existing_record is None:
            return False
        session.delete(existing_record)
        session.commit()
        return True

    @with_session
    def getAttendanceByScheduleId(self, session, schedule_id: int) -> Optional[List[Type[AttendanceDB]]]:
        attendance_db: List[Type[AttendanceDB]] = session.query(AttendanceDB).filter_by(schedule_id=schedule_id).all()
        if attendance_db is None:
            return None
        return attendance_db

    @with_session
    def getStudentAttendanceByScheduleId(self, session, student_id: int, schedule_id: int) -> Optional[AttendanceDB]:
        attendance_db: Optional[AttendanceDB] = session.query(AttendanceDB).filter_by(schedule_id=schedule_id,
                                                                                      student_id=student_id).first()
        if attendance_db is None:
            return None
        return attendance_db
