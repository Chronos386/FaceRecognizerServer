import cv2
import json
import numpy as np
from pathlib import Path
from collections import Counter
from typing import Optional, Tuple, List
from werkzeug.datastructures import FileStorage
from source_code.utils.logger_file import logger
from datetime import datetime, timedelta, time, date
from source_code.db_connection.db_class import DBClass
from source_code.db_connection.db_models.rooms_db import RoomsDB
from source_code.db_connection.db_models.groups_db import GroupsDB
from source_code.api_connection.send_models.send_room import SendRoom
from source_code.db_connection.db_models.accounts_db import AccountsDB
from source_code.db_connection.db_models.schedule_db import ScheduleDB
from source_code.db_connection.db_models.students_db import StudentsDB
from source_code.db_connection.db_models.subjects_db import SubjectsDB
from source_code.db_connection.db_models.teachers_db import TeachersDB
from source_code.api_connection.send_models.send_group import SendGroup
from source_code.face_recognition.face_recognizer import FaceRecognizer
from source_code.db_connection.db_models.buildings_db import BuildingsDB
from source_code.db_connection.db_models.attendance_db import AttendanceDB
from source_code.db_connection.db_models.institutes_db import InstitutesDB
from source_code.api_connection.send_models.send_subject import SendSubject
from source_code.api_connection.send_models.send_teacher import SendTeacher
from source_code.api_connection.send_models.send_account import SendAccount
from source_code.db_connection.db_models.departments_db import DepartmentsDB
from source_code.api_connection.analytics_processor import AnalyticsProcessor
from source_code.api_connection.send_models.send_students import SendStudents
from source_code.api_connection.send_models.send_schedule import SendSchedule
from source_code.api_connection.send_models.send_buildings import SendBuildings
from source_code.api_connection.send_models.send_attendance import SendAttendance
from source_code.api_connection.send_models.send_institutes import SendInstitutes
from source_code.api_connection.send_models.send_departments import SendDepartments
from source_code.db_connection.db_models.face_embeddings_db import FaceEmbeddingsDB
from source_code.api_connection.send_models.send_device_message import SendDeviceMessage


class ApiConnector:
    def __init__(self, db_class: DBClass, face_recognizer: FaceRecognizer, processor: AnalyticsProcessor):
        self.db_class = db_class
        self.face_recognizer = face_recognizer
        self.processor = processor

    #  |=========================Приватная функция для получения начала и конца недели=========================|
    @staticmethod
    def __getWeekRange(week_date: datetime) -> Tuple[date, date]:
        weekday = week_date.weekday()
        start_of_week = week_date - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week.date(), end_of_week.date()

    #  |======================================Приватные функции. Аккаунт======================================|
    def __handleStudentLogin(self, account: AccountsDB, key: str, student: StudentsDB) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return None
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(group.institute_id)
        if institute is None:
            return None
        send = SendAccount(id_=account.id, is_admin=account.admin, login=account.email, name=student.name, key=key,
                           group_id=group.id, group_name=group.name, institute_id=institute.id,
                           institute_name=institute.name)
        return send.toJson()

    def __handleTeacherLogin(self, account: AccountsDB, key: str, teacher: TeachersDB) -> Optional[str]:
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(teacher.department_id)
        if department is None:
            return None
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(department.institute_id)
        if institute is None:
            return None
        send = SendAccount(id_=account.id, is_admin=account.admin, login=account.email, name=teacher.name, key=key,
                           department_id=department.id, department_name=department.name, institute_id=institute.id,
                           institute_name=institute.name)
        return send.toJson()

    #  |======================================Приватные функции. Студент======================================|
    @staticmethod
    def __findDuplicateStudent(students) -> Optional[StudentsDB]:
        id_counts = Counter(student.id for student in students)
        duplicate_ids = [student_id for student_id, count in id_counts.items() if count >= 2]
        if duplicate_ids:
            duplicated_id = duplicate_ids[0]
            for student in students:
                if student.id == duplicated_id:
                    return student
        return None

    def __handleGetStudentByPhoto(self, photo: FileStorage) -> Tuple[Optional[StudentsDB], int]:
        emb: List[FaceEmbeddingsDB] = self.db_class.getAllEmbeddings()
        if len(emb) == 0:
            return None, 5
        emb_list_p = [np.array(emb_elem.embedding, dtype='float32') for emb_elem in emb]
        emb_list_combined = np.vstack(emb_list_p)

        emb_numbers, code = self.face_recognizer.recognizeFace(photo, emb_list_combined)
        if code != 0:
            return None, code
        students_list: List[StudentsDB] = []
        for emb_numb in emb_numbers:
            student = self.db_class.getStudentByID(emb[emb_numb].student_id)
            if student is not None:
                students_list.append(student)
        if len(students_list) == 0:
            return None, 6
        elif len(students_list) == 1:
            return students_list[0], 0
        student = self.__findDuplicateStudent(students_list)
        return student, 0

    #  |====================================Приватные функции. Расписание====================================|
    def __handleGetGroupSchedule(self, group: GroupsDB, week_start: date, week_end: date) -> Optional[str]:
        schedule_list: Optional[List[ScheduleDB]] = self.db_class.getScheduleForGroup(
            group_id=group.id, week_start=week_start, week_end=week_end
        )
        schedule_dicts: List[dict] = []
        for schedule in schedule_list:
            subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(schedule.subject_id)
            if subject is None:
                continue
            teacher: Optional[TeachersDB] = self.db_class.getTeacherByID(schedule.teacher_id)
            if teacher is None:
                continue
            new_room: Optional[RoomsDB] = self.db_class.getRoomByID(schedule.room_id)
            if new_room is None:
                continue
            building: Optional[BuildingsDB] = self.db_class.getBuildingByID(new_room.building_id)
            if new_room is None:
                continue
            schedule_dicts.append(
                SendSchedule(
                    id_=schedule.id,
                    date=datetime.combine(schedule.date, time()),
                    time_start=schedule.time_start,
                    time_end=schedule.time_end,
                    group=group.name,
                    group_id=group.id,
                    subject=subject.name,
                    subject_id=subject.id,
                    teacher=teacher.name,
                    teacher_id=teacher.id,
                    room=new_room.number,
                    room_id=new_room.id,
                    building=building.name,
                    building_id=building.id
                ).toDict()
            )
        return json.dumps(schedule_dicts, ensure_ascii=False)

    def __handleGetStudentSchedule(self, student: StudentsDB, week_start: date, week_end: date) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return None
        return self.__handleGetGroupSchedule(group, week_start, week_end)

    def __handleGetTeacherSchedule(self, teacher: TeachersDB, week_start: date, week_end: date) -> Optional[str]:
        schedule_list: Optional[List[ScheduleDB]] = self.db_class.getScheduleForTeacher(
            teacher_id=teacher.id, week_start=week_start, week_end=week_end
        )
        schedule_dicts: List[dict] = []
        for schedule in schedule_list:
            subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(schedule.subject_id)
            if subject is None:
                continue
            new_room: Optional[RoomsDB] = self.db_class.getRoomByID(schedule.room_id)
            if new_room is None:
                continue
            group: Optional[GroupsDB] = self.db_class.getGroupByID(schedule.group_id)
            if group is None:
                return None
            building: Optional[BuildingsDB] = self.db_class.getBuildingByID(new_room.building_id)
            if new_room is None:
                return None
            schedule_dicts.append(
                SendSchedule(
                    id_=schedule.id,
                    date=datetime.combine(schedule.date, time()),
                    time_start=schedule.time_start,
                    time_end=schedule.time_end,
                    group=group.name,
                    group_id=group.id,
                    subject=subject.name,
                    subject_id=subject.id,
                    teacher=teacher.name,
                    teacher_id=teacher.id,
                    room=new_room.number,
                    room_id=new_room.id,
                    building=building.name,
                    building_id=building.id
                ).toDict()
            )
        return json.dumps(schedule_dicts, ensure_ascii=False)

    #  |============================================Хэши============================================|
    def deleteAllHashes(self):
        self.db_class.deleteAllHashes()
        return

    def checkIsAdminByHash(self, hash_admin: str) -> Optional[bool]:
        account = self.db_class.getAccByHash(hash_admin)
        if account is None:
            return None
        return account.admin

    #  |==========================================Аккаунт==========================================|
    def getAccIdByHash(self, key: str) -> Optional[int]:
        account: Optional[AccountsDB] = self.db_class.getAccByHash(key)
        if account is None:
            return None
        return account.id

    def loginByPassword(self, login: str, password: str) -> Optional[str]:
        account_tuple: Optional[Tuple[AccountsDB, str]] = self.db_class.loginByPassword(login, password)
        if account_tuple is None:
            return None
        student = self.db_class.getStudentByAccID(account_tuple[0].id)
        if student:
            return self.__handleStudentLogin(account_tuple[0], account_tuple[1], student)
        teacher = self.db_class.getTeacherByAccID(account_tuple[0].id)
        if teacher:
            return self.__handleTeacherLogin(account_tuple[0], account_tuple[1], teacher)
        return None

    def loginByHash(self, key: str) -> Optional[str]:
        account: Optional[AccountsDB] = self.db_class.getAccByHash(key)
        if account is None:
            return None
        student: Optional[StudentsDB] = self.db_class.getStudentByAccID(account.id)
        if student:
            return self.__handleStudentLogin(account, key, student)
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByAccID(account.id)
        if teacher:
            return self.__handleTeacherLogin(account, key, teacher)
        return None

    def logoutByHash(self, key: str) -> bool:
        return self.db_class.logoutByHash(key)

    #  |==========================================Институт==========================================|
    def getAllInstitutes(self) -> Optional[str]:
        institutes_db: Optional[List[InstitutesDB]] = self.db_class.getAllInstitutes()
        if institutes_db is None:
            return None
        institutes_dicts: List[dict] = []
        for institute in institutes_db:
            institutes_dicts.append(SendInstitutes(institute.id, institute.name).toDict())
        return json.dumps(institutes_dicts, ensure_ascii=False)

    def getInstitute(self, institute_id: int) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(institute_id)
        if institute is None:
            return None
        institute_dict: dict = SendInstitutes(institute.id, institute.name).toDict()
        return json.dumps(institute_dict, ensure_ascii=False)

    def createInstitute(self, name: str) -> Optional[str]:
        new_institute = self.db_class.createInstitute(name=name)
        if new_institute is None:
            return None
        institute_dict = SendInstitutes(new_institute.id, new_institute.name).toDict()
        return json.dumps(institute_dict, ensure_ascii=False)

    def updateInstitute(self, id_institute: int, name: str) -> Optional[str]:
        updated_institute = self.db_class.updateInstitute(institute_id=id_institute, name=name)
        if updated_institute is None:
            return None
        institute_dict = SendInstitutes(updated_institute.id, updated_institute.name).toDict()
        return json.dumps(institute_dict, ensure_ascii=False)

    def deleteInstitute(self, id_institute: int) -> int:
        check = self.db_class.deleteInstitute(institute_id=id_institute)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Кафедра==========================================|
    def getAllDepartmentsByInstitute(self, id_institute: int) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(id_institute)
        if institute is None:
            return None
        departments_db: Optional[List[DepartmentsDB]] = self.db_class.getAllDepartmentsByInstitute(id_institute)
        if departments_db is None:
            return None
        departments_dicts: List[dict] = []
        for department in departments_db:
            departments_dicts.append(SendDepartments(department.id, department.name, institute.name,
                                                     institute.id).toDict())
        return json.dumps(departments_dicts, ensure_ascii=False)

    def getDepartment(self, department_id: int) -> Optional[str]:
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(department_id)
        if department is None:
            return None
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(department.institute_id)
        if institute is None:
            return None
        department_dict = SendDepartments(department.id, department.name, institute.name, institute.id).toDict()
        return json.dumps(department_dict, ensure_ascii=False)

    def createDepartment(self, id_institute: int, name: str) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(id_institute)
        if institute is None:
            return None
        new_department = self.db_class.createDepartment(id_institute=institute.id, name=name)
        if new_department is None:
            return None
        department_dict = SendDepartments(new_department.id, new_department.name, institute.name, institute.id).toDict()
        return json.dumps(department_dict, ensure_ascii=False)

    def updateDepartment(self, id_department: int, id_institute: int, name: str) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(id_institute)
        if institute is None:
            return None
        updated_department = self.db_class.updateDepartment(id_department, institute.id, name)
        if updated_department is None:
            return None
        department_dict = SendDepartments(updated_department.id, updated_department.name,
                                          institute.name, institute.id).toDict()
        return json.dumps(department_dict, ensure_ascii=False)

    def deleteDepartment(self, id_department: int) -> int:
        check = self.db_class.deleteDepartment(id_department=id_department)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Преподаватель==========================================|
    def getAllTeachersByDepartment(self, department_id: int) -> Optional[str]:
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(department_id)
        if department is None:
            return None
        teachers_db: List[TeachersDB] = self.db_class.getAllTeachersByDepartment(department_id)
        if teachers_db is None:
            return None
        teachers_dicts: List[dict] = []
        for teacher in teachers_db:
            teachers_dicts.append(SendTeacher(teacher.id, teacher.name, teacher.acc_id, department.name,
                                              teacher.department_id).toDict())
        return json.dumps(teachers_dicts, ensure_ascii=False)

    def getTeacher(self, teacher_id) -> Optional[str]:
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByID(teacher_id)
        if teacher is None:
            return None
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(teacher.department_id)
        if department is None:
            return None
        teacher_dict: dict = SendTeacher(teacher.id, teacher.name, teacher.acc_id, department.name,
                                         department.id).toDict()
        return json.dumps(teacher_dict, ensure_ascii=False)

    def createTeacher(self, name: str, email: str, password: str, department_id: int) -> Optional[str]:
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(department_id)
        if department is None:
            return None
        new_acc = self.db_class.createAccount(email=email, password=password)
        if new_acc is None:
            return None
        teacher = self.db_class.createTeacher(name=name, acc_id=new_acc.id, department_id=department_id)
        if teacher is None:
            self.db_class.deleteAccount(new_acc.id)
            return None
        teacher_dicts = SendTeacher(teacher.id, teacher.name, teacher.acc_id, department.name,
                                    teacher.department_id).toDict()
        return json.dumps(teacher_dicts, ensure_ascii=False)

    def updateTeacher(self, id_teacher: int, name: str, department_id: int) -> Optional[str]:
        department: Optional[DepartmentsDB] = self.db_class.getDepartmentByID(department_id)
        if department is None:
            return None
        teacher = self.db_class.updateTeacher(id_teacher, name, department.id)
        if teacher is None:
            return None
        teacher_dicts = SendTeacher(teacher.id, teacher.name, teacher.acc_id, department.name,
                                    teacher.department_id).toDict()
        return json.dumps(teacher_dicts, ensure_ascii=False)

    def deleteTeacher(self, id_teacher: int) -> int:
        check = self.db_class.deleteTeacher(id_teacher=id_teacher)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Группа==========================================|
    def getAllGroupsByInstitute(self, institute_id: int):
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(institute_id)
        if institute is None:
            return None
        groups_db: List[GroupsDB] = self.db_class.getAllGroupsByInstitute(institute.id)
        if groups_db is None:
            return None
        groups_dicts: List[dict] = []
        for group in groups_db:
            groups_dicts.append(SendGroup(group.id, group.name, group.institute_id).toDict())
        return json.dumps(groups_dicts, ensure_ascii=False)

    def getGroup(self, group_id: int) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        group_dicts = SendGroup(group.id, group.name, group.institute_id).toDict()
        return json.dumps(group_dicts, ensure_ascii=False)

    def createGroup(self, id_institute: int, name: str) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(id_institute)
        if institute is None:
            return None
        new_group = self.db_class.createGroup(id_institute=institute.id, name=name)
        if new_group is None:
            return None
        group_dict = SendGroup(new_group.id, new_group.name, new_group.institute_id).toDict()
        return json.dumps(group_dict, ensure_ascii=False)

    def updateGroup(self, group_id: int, name: str, id_institute: int) -> Optional[str]:
        institute: Optional[InstitutesDB] = self.db_class.getInstituteByID(id_institute)
        if institute is None:
            return None
        group = self.db_class.updateGroup(group_id, name, institute.id)
        if group is None:
            return None
        group_dict = SendGroup(group.id, group.name, group.institute_id).toDict()
        return json.dumps(group_dict, ensure_ascii=False)

    def deleteGroup(self, group_id: int) -> int:
        check = self.db_class.deleteGroup(group_id=group_id)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Студент==========================================|
    def getAllStudentsByGroup(self, group_id: int) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        students: Optional[List[StudentsDB]] = self.db_class.getAllStudentsByGroup(group_id)
        if students is None:
            return None
        students_dicts: List[dict] = []
        for student in students:
            students_dicts.append(
                SendStudents(id_=student.id, name=student.name, group=group.name, group_id=group.id,
                             acc_id=student.acc_id).toDict()
            )
        return json.dumps(students_dicts, ensure_ascii=False)

    def getStudent(self, student_id: int) -> Optional[str]:
        student: Optional[StudentsDB] = self.db_class.getStudentByID(student_id)
        if student is None:
            return None
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return None
        student_dict: dict = SendStudents(student.id, student.name, student.acc_id, group.name, group.id).toDict()
        return json.dumps(student_dict, ensure_ascii=False)

    def createStudent(self, name: str, email: str, password: str, group_id: int) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        new_acc = self.db_class.createAccount(email=email, password=password)
        if new_acc is None:
            return None
        student = self.db_class.createStudent(name=name, acc_id=new_acc.id, group_id=group_id)
        if student is None:
            self.db_class.deleteAccount(new_acc.id)
            return None
        student_dicts = SendStudents(student.id, student.name, student.acc_id, group.name, student.group_id).toDict()
        return json.dumps(student_dicts, ensure_ascii=False)

    def updateStudent(self, student_id: int, name: str, group_id: int) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        student = self.db_class.updateStudent(student_id, name, group.id)
        if student is None:
            return None
        group_dict = SendStudents(student.id, student.name, student.acc_id, group.name, student.group_id).toDict()
        return json.dumps(group_dict, ensure_ascii=False)

    def deleteStudent(self, student_id: int) -> int:
        check = self.db_class.deleteStudent(student_id=student_id)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Эмбиддинги===========================================|
    @staticmethod
    def __sanitizeFilename(name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

    def createEmbedding(self, photo: FileStorage, student_id: int) -> int:
        file_bytes = photo.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        photo.seek(0)

        student: Optional[StudentsDB] = self.db_class.getStudentByID(student_id)
        if student is None:
            return -1
        emb, code = self.face_recognizer.getEmbedding(img)
        if code != 0:
            return code
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return -1
        try:
            project_root = Path(__file__).parent.parent.parent
            known_faces_path = project_root / 'known_faces'

            group_folder = known_faces_path / self.__sanitizeFilename(group.name)
            group_folder.mkdir(parents=True, exist_ok=True)

            student_folder = group_folder / self.__sanitizeFilename(student.name)
            student_folder.mkdir(parents=True, exist_ok=True)

            existing_files = list(student_folder.glob('*.jpeg'))
            existing_numbers = [int(f.stem) for f in existing_files if f.stem.isdigit()]
            next_number = 1
            while next_number in existing_numbers:
                next_number += 1
            filename = student_folder / f"{next_number}.jpeg"
            photo.save(str(filename))

            self.db_class.createEmbedding(embedding=emb, student_id=student.id, path_photo=str(filename))
            return 0
        except Exception as e:
            logger.error(f"Ошибка при сохранении фотографии: {e}")
            return -1

    #  |==========================================Предмет==========================================|
    def getAllSubjects(self) -> Optional[str]:
        subjects: Optional[List[SubjectsDB]] = self.db_class.getAllSubjects()
        if subjects is None:
            return None
        subjects_dicts: List[dict] = []
        for subject in subjects:
            subjects_dicts.append(SendSubject(subject.id, subject.name).toDict())
        return json.dumps(subjects_dicts, ensure_ascii=False)

    def getSubject(self, subject_id: int) -> Optional[str]:
        subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(subject_id)
        if subject is None:
            return None
        subject_dict: dict = SendSubject(subject.id, subject.name).toDict()
        return json.dumps(subject_dict, ensure_ascii=False)

    def createSubject(self, name: str) -> Optional[str]:
        subject: Optional[SubjectsDB] = self.db_class.createSubject(name=name)
        if subject is None:
            return None
        subject_dict: dict = SendSubject(subject.id, subject.name).toDict()
        return json.dumps(subject_dict, ensure_ascii=False)

    def updateSubject(self, subject_id: int, name: str) -> Optional[str]:
        subject: Optional[SubjectsDB] = self.db_class.updateSubject(subject_id, name=name)
        if subject is None:
            return None
        subject_dict: dict = SendSubject(subject.id, subject.name).toDict()
        return json.dumps(subject_dict, ensure_ascii=False)

    def deleteSubject(self, subject_id: int) -> int:
        check = self.db_class.deleteSubject(subject_id=subject_id)
        if check:
            return 200
        else:
            return 500

    #  |============================================Корпус============================================|
    def getAllBuildings(self) -> Optional[str]:
        buildings: List[BuildingsDB] = self.db_class.getAllBuildings()
        if buildings is None:
            return None
        buildings_dicts: List[dict] = []
        for building in buildings:
            buildings_dicts.append(SendBuildings(building.id, building.name, building.address).toDict())
        return json.dumps(buildings_dicts, ensure_ascii=False)

    def getBuilding(self, building_id: int) -> Optional[str]:
        building: Optional[BuildingsDB] = self.db_class.getBuildingByID(building_id)
        if building is None:
            return None
        building_dict: dict = SendBuildings(building.id, building.name, building.address).toDict()
        return json.dumps(building_dict, ensure_ascii=False)

    def createBuilding(self, name: str, address: str) -> Optional[str]:
        building: BuildingsDB = self.db_class.createBuilding(name=name, address=address)
        if building is None:
            return None
        building_dict: dict = SendBuildings(building.id, building.name, building.address).toDict()
        return json.dumps(building_dict, ensure_ascii=False)

    def updateBuilding(self, building_id: int, name: str, address: str) -> Optional[str]:
        building = self.db_class.updateBuilding(building_id, name=name, address=address)
        if building is None:
            return None
        building_dict: dict = SendBuildings(building.id, building.name, building.address).toDict()
        return json.dumps(building_dict, ensure_ascii=False)

    def deleteBuilding(self, building_id: int) -> int:
        check = self.db_class.deleteBuilding(building_id=building_id)
        if check:
            return 200
        else:
            return 500

    #  |============================================Кабинет============================================|
    def getAllRoomsByBuilding(self, building_id: int) -> Optional[str]:
        rooms: Optional[List[RoomsDB]] = self.db_class.getAllRoomsByBuilding(building_id)
        if rooms is None:
            return None
        rooms_dicts: List[dict] = []
        for room in rooms:
            device_id = self.db_class.checkDeviceByRoomID(room_id=room.id)
            rooms_dicts.append(SendRoom(room.id, room.number, room.building_id, device_id).toDict())
        return json.dumps(rooms_dicts, ensure_ascii=False)

    def getRoom(self, room_id: int) -> Optional[str]:
        room: Optional[RoomsDB] = self.db_class.getRoomByID(room_id)
        if room is None:
            return None
        device_id = self.db_class.checkDeviceByRoomID(room_id=room.id)
        room_dict: dict = SendRoom(room.id, room.number, room.building_id, device_id).toDict()
        return json.dumps(room_dict, ensure_ascii=False)

    def createRoom(self, number: str, building_id: int) -> Optional[str]:
        building = self.db_class.getBuildingByID(building_id)
        if building is None:
            return None
        room = self.db_class.createRoom(number=number, building_id=building.id)
        if room is None:
            return None
        room_dict: dict = SendRoom(room.id, room.number, room.building_id).toDict()
        return json.dumps(room_dict, ensure_ascii=False)

    def updateRoom(self, room_id: int, number: str, building_id: int) -> Optional[str]:
        building = self.db_class.getBuildingByID(building_id)
        if building is None:
            return None
        room = self.db_class.updateRoom(room_id=room_id, number=number, building_id=building.id)
        room_dict: dict = SendRoom(room.id, room.number, room.building_id).toDict()
        return json.dumps(room_dict, ensure_ascii=False)

    def deleteRoom(self, room_id: int) -> int:
        check = self.db_class.deleteRoom(room_id=room_id)
        if check:
            return 200
        else:
            return 500

    #  |==============================================Девайс==============================================|
    def createDevice(self, room_id) -> Optional[str]:
        room: Optional[RoomsDB] = self.db_class.getRoomByID(room_id)
        if room is None:
            return None
        device = self.db_class.createDevice(room_id=room_id)
        if device is None:
            return None
        room_dict: dict = SendRoom(room.id, room.number, room.building_id, device.id).toDict()
        return json.dumps(room_dict, ensure_ascii=False)

    def deleteDevice(self, device_id: int) -> int:
        check = self.db_class.deleteDevice(device_id=device_id)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Расписание==========================================|
    def getStudentScheduleByPhoto(self, photo: FileStorage) -> Tuple[Optional[int], Optional[str], int]:
        student, code = self.__handleGetStudentByPhoto(photo)
        if code != 0:
            return None, None, code
        today: datetime = datetime.today()
        week_start, week_end = self.__getWeekRange(today)
        return student.id, self.__handleGetStudentSchedule(student, week_start, week_end), 0

    def getStudentScheduleByHash(self, acc_id: int, week_start: date, week_end: date) -> Optional[str]:
        student: Optional[StudentsDB] = self.db_class.getStudentByAccID(acc_id)
        if student is None:
            return None
        return self.__handleGetStudentSchedule(student, week_start, week_end)

    def getTeacherScheduleByHash(self, acc_id: int, week_start: date, week_end: date) -> Optional[str]:
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByAccID(acc_id)
        if teacher is None:
            return None
        return self.__handleGetTeacherSchedule(teacher, week_start, week_end)

    def getTeacherScheduleByTeacherId(self, teacher_id: int, week_start: date, week_end: date) -> Optional[str]:
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByID(teacher_id)
        if teacher is None:
            return None
        return self.__handleGetTeacherSchedule(teacher, week_start, week_end)

    def getGroupScheduleById(self, group_id: int, week_start: date, week_end: date) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        return self.__handleGetGroupSchedule(group, week_start, week_end)

    def createSchedule(self, date_schedule: date, time_start: time, time_end: time, group_id: int, subject_id: int,
                       teacher_id: int, room_id: int) -> Optional[str]:
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(subject_id)
        if subject is None:
            return None
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByID(teacher_id)
        if teacher is None:
            return None
        room: Optional[RoomsDB] = self.db_class.getRoomByID(room_id)
        if room is None:
            return None
        building = self.db_class.getBuildingByID(room.building_id)
        if building is None:
            return None
        schedule = self.db_class.createSchedule(date_schedule=date_schedule, time_start=time_start, time_end=time_end,
                                                group_id=group.id, subject_id=subject.id, teacher_id=teacher.id,
                                                room_id=room.id)
        if schedule is None:
            return None
        schedule_dict: dict = SendSchedule(id_=schedule.id, date=datetime.combine(schedule.date, time()),
                                           time_start=schedule.time_start, time_end=schedule.time_end,
                                           group=group.name, group_id=group.id, subject=subject.name,
                                           subject_id=subject.id, teacher=teacher.name, teacher_id=teacher.id,
                                           room=room.number, room_id=room.id, building=building.name,
                                           building_id=building.id).toDict()
        return json.dumps(schedule_dict, ensure_ascii=False)

    def updateSchedule(self, schedule_id: int, date_schedule: date, time_start: time, time_end: time, group_id: int,
                       subject_id: int, teacher_id: int, room_id: int):
        group: Optional[GroupsDB] = self.db_class.getGroupByID(group_id)
        if group is None:
            return None
        subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(subject_id)
        if subject is None:
            return None
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByID(teacher_id)
        if teacher is None:
            return None
        room: Optional[RoomsDB] = self.db_class.getRoomByID(room_id)
        if room is None:
            return None
        building = self.db_class.getBuildingByID(room.building_id)
        if building is None:
            return None
        schedule = self.db_class.updateSchedule(date_schedule=date_schedule, time_start=time_start, time_end=time_end,
                                                group_id=group.id, subject_id=subject.id, teacher_id=teacher.id,
                                                room_id=room.id, schedule_id=schedule_id)
        if schedule is None:
            return None
        schedule_dict: dict = SendSchedule(id_=schedule.id, date=datetime.combine(schedule.date, time()),
                                           time_start=schedule.time_start, time_end=schedule.time_end,
                                           group=group.name, group_id=group.id, subject=subject.name,
                                           subject_id=subject.id, teacher=teacher.name, teacher_id=teacher.id,
                                           room=room.number, room_id=room.id, building=building.name,
                                           building_id=building.id).toDict()
        return json.dumps(schedule_dict, ensure_ascii=False)

    def deleteSchedule(self, schedule_id: int) -> int:
        check = self.db_class.deleteSchedule(schedule_id=schedule_id)
        if check:
            return 200
        else:
            return 500

    #  |==========================================Посещаемость==========================================|
    def markAttendanceByPhoto(self, photo: FileStorage, current_datetime: datetime,
                              device_id: int) -> Tuple[int, Optional[int], Optional[int], Optional[str]]:
        room: RoomsDB = self.db_class.getRoomByDeviceID(device_id)
        if room is None:
            return 402, None, None, None  # Устройство не зарегистрировано
        student, code = self.__handleGetStudentByPhoto(photo)
        if code != 0:
            return code, None, None, None  # Не распознан
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return 500, student.id, None, None  # Ошибка БД
        schedule: Optional[ScheduleDB] = self.db_class.getScheduleForAttendance(group.id, room.id, current_datetime)
        if schedule is None:
            return 505, student.id, None, None  # Нет подходящих занятий
        subject: Optional[SubjectsDB] = self.db_class.getSubjectByID(schedule.subject_id)
        if subject is None:
            return 500, student.id, None, None  # Ошибка БД
        self.db_class.markAttendance(student.id, schedule.id, True)
        return 200, student.id, schedule.id, SendDeviceMessage(
            schedule_id=schedule.id, student_id=student.id, name=student.name, group_name=group.name,
            subject_name=subject.name,
        ).toJson()

    def cancelMarkAttendanceByPhoto(self, student_id: int, schedule_id: int, device_id: int) -> int:
        room: RoomsDB = self.db_class.getRoomByDeviceID(device_id)
        if room is None:
            return 402
        schedule: Optional[ScheduleDB] = self.db_class.getScheduleByID(schedule_id)
        if schedule is None:
            return 500
        student: Optional[StudentsDB] = self.db_class.getStudentByID(student_id)
        if student is None:
            return 500
        result: bool = self.db_class.deleteWrongAttendance(student.id, schedule.id)
        if result:
            return 200
        return 500

    def martAttendanceByTeacher(self, acc_id: int, student_id: int, schedule_id: int, status: bool) -> int:
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByAccID(acc_id)
        if teacher is None:
            return 401
        student = self.db_class.getStudentByID(student_id)
        if student is None:
            return 500
        schedule: Optional[ScheduleDB] = self.db_class.getScheduleByID(schedule_id)
        if schedule is None:
            return 500
        if teacher.id != schedule.teacher_id:
            return 403
        self.db_class.markAttendance(student.id, schedule.id, status)
        return 200

    def markAbsenceAttendance(self):
        current_datetime = datetime.now()
        missed_schedules: Optional[List[ScheduleDB]] = self.db_class.getMissedSchedules(current_datetime)
        if missed_schedules is None:
            return
        for schedule in missed_schedules:
            students_without_attendance = self.db_class.getStudentsWithoutAttendance(schedule.id)
            if students_without_attendance is None:
                continue
            for student in students_without_attendance:
                self.db_class.markAttendance(student.id, schedule.id, status=False)

    def getAttendanceGroupBySchedule(self, acc_id: int, schedule_id: int) -> Tuple[int, Optional[str]]:
        teacher: Optional[TeachersDB] = self.db_class.getTeacherByAccID(acc_id)
        if teacher is None:
            return 401, None
        schedule: Optional[ScheduleDB] = self.db_class.getScheduleByID(schedule_id)
        if schedule is None:
            return 500, None
        if schedule.teacher_id != teacher.id:
            return 403, None
        attendance_db: Optional[List[AttendanceDB]] = self.db_class.getAttendanceByScheduleId(schedule_id)
        if attendance_db is None:
            return 500, None
        attendance_dicts: List[dict] = []
        for attendance in attendance_db:
            student = self.db_class.getStudentByID(attendance.student_id)
            if student is None:
                continue
            if student.group_id == schedule.group_id:
                attendance_dicts.append(SendAttendance(
                    id_=attendance.id, status=attendance.status, student_id=attendance.student_id,
                    schedule_id=attendance.schedule_id).toDict()
                                        )
        return 200, json.dumps(attendance_dicts, ensure_ascii=False)

    def getStudentAttendance(self, acc_id: int, week_start: date, week_end: date) -> Tuple[int, Optional[str]]:
        student: Optional[StudentsDB] = self.db_class.getStudentByAccID(acc_id)
        if student is None:
            return 403, None
        group: Optional[GroupsDB] = self.db_class.getGroupByID(student.group_id)
        if group is None:
            return 500, None
        schedule_list: Optional[List[ScheduleDB]] = self.db_class.getScheduleForGroup(
            group_id=group.id, week_start=week_start, week_end=week_end
        )
        if schedule_list is None:
            return 500, None
        attendance_dicts: List[dict] = []
        for schedule in schedule_list:
            attendance: Optional[AttendanceDB] = self.db_class.getStudentAttendanceByScheduleId(student.id, schedule.id)
            attendance_dicts.append(SendAttendance(
                id_=attendance.id, status=attendance.status, student_id=attendance.student_id,
                schedule_id=attendance.schedule_id).toDict()
                                    )
        return 200, json.dumps(attendance_dicts, ensure_ascii=False)

    #  |==========================================Аналитика==========================================|
    # 1. Получение динамики посещаемости университета
    def getUniversityAttendanceDynamic(self, start_date: date, end_date: date) -> str:
        data = self.processor.get_university_dynamic(start_date, end_date)
        return json.dumps([item.toDict() for item in data], ensure_ascii=False)

    # 2. Получение динамики посещаемости группы
    def getGroupAttendanceDynamic(self, group_id: int, start_date: date, end_date: date) -> str:
        data = self.processor.get_group_dynamic(group_id, start_date, end_date)
        return json.dumps([item.toDict() for item in data], ensure_ascii=False)

    # 3. Кластеризация студентов группы
    def getGroupClusters(self, group_id: int, start_date: date, end_date: date) -> str:
        clusters = self.processor.cluster_group_students(group_id, start_date, end_date)
        result = {
            "clusters": {
                name: [s.toDict() for s in students]
                for name, students in clusters.items()
            }
        }
        return json.dumps(result, ensure_ascii=False)

    # 4. Анализ институтов
    def getInstitutesAnalysis(self, start_date: date, end_date: date) -> str:
        analysis = self.processor.analyze_institutes_attendance(start_date, end_date)
        return json.dumps([a.toDict() for a in analysis], ensure_ascii=False)

    # 5. Топ преподавателей по посещаемости
    def getTopTeachersAttendance(self, start_date: date, end_date: date) -> str:
        top_teachers = self.processor.get_top_teachers_attendance(start_date, end_date)
        if not top_teachers:
            return json.dumps([], ensure_ascii=False)
        return json.dumps([t.toDict() for t in top_teachers], ensure_ascii=False)

    # 6. Топ студентов по пропускам
    def getTopStudentsAbsences(self, start_date: date, end_date: date) -> str:
        top_students = self.processor.get_top_students_absences(start_date, end_date)
        if not top_students:
            return json.dumps([], ensure_ascii=False)
        return json.dumps([s.toDict() for s in top_students], ensure_ascii=False)

    # 7. Топ групп по пропускам
    def getTopGroupsAbsences(self, start_date: date, end_date: date) -> str:
        top_groups = self.processor.get_top_groups_absences(start_date, end_date)
        if not top_groups:
            return json.dumps([], ensure_ascii=False)
        return json.dumps([g.toDict() for g in top_groups], ensure_ascii=False)

    # 8. Топ групп по посещаемости
    def getTopGroupsAttendance(self, start_date: date, end_date: date) -> str:
        top_groups = self.processor.get_top_groups_by_attendance(start_date, end_date)
        if not top_groups:
            return json.dumps([], ensure_ascii=False)
        result = [group.toDict() for group in top_groups]
        return json.dumps(result, ensure_ascii=False)
