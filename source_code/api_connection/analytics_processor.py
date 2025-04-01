from typing import List, Dict
from sqlalchemy import func, case
from datetime import date, timedelta
from source_code.db_connection.db_class import DBClass
from source_code.db_connection.db_models.groups_db import GroupsDB
from source_code.db_connection.db_models.schedule_db import ScheduleDB
from source_code.db_connection.db_models.students_db import StudentsDB
from source_code.db_connection.db_models.teachers_db import TeachersDB
from source_code.db_connection.db_models.attendance_db import AttendanceDB
from source_code.api_connection.send_models.send_group_absences import SendGroupAbsences
from source_code.api_connection.send_models.send_student_cluster import SendStudentCluster
from source_code.api_connection.send_models.send_student_absences import SendStudentAbsences
from source_code.api_connection.send_models.send_group_attendance import SendGroupAttendance
from source_code.api_connection.send_models.send_institute_analysis import SendInstituteAnalysis
from source_code.api_connection.send_models.send_teacher_attendance import SendTeacherAttendance
from source_code.api_connection.send_models.attendance_daily_dynamic import AttendanceDailyDynamic


class AnalyticsProcessor:
    def __init__(self, db_class: DBClass):
        self.db_class = db_class

    def _get_daily_dynamic(self, start_date: date, end_date: date, group_id: int = None) -> List[AttendanceDailyDynamic]:
        delta = end_date - start_date
        results = []
        # Генерируем все даты в диапазоне
        date_range = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
        # Делаем единый запрос для всех дат
        query = self.db_class.session.query(
            ScheduleDB.date,
            func.sum(case((AttendanceDB.status == True, 1), else_=0)).label('attended'),
            func.count(AttendanceDB.id).label('total')
        ).join(AttendanceDB, ScheduleDB.id == AttendanceDB.schedule_id)
        if group_id:
            query = (query.join(StudentsDB, AttendanceDB.student_id == StudentsDB.id)
                     .filter(StudentsDB.group_id == group_id))
        query = (query.filter(ScheduleDB.date.between(start_date, end_date))
                 .group_by(ScheduleDB.date).order_by(ScheduleDB.date))
        # Собираем результаты в словарь для быстрого доступа
        db_results = {res.date: (res.attended, res.total) for res in query.all()}
        # Заполняем все даты в диапазоне
        for single_date in date_range:
            if single_date.weekday() >= 5:
                continue
            attended, total = db_results.get(single_date, (0, 0))
            percent = (attended / total * 100) if total > 0 else 0.0
            results.append(
                AttendanceDailyDynamic(
                    date_=single_date,
                    attendance_per=percent,
                    attended=attended,
                    total=total
                )
            )
        return results

    # 1. Получение динамики посещаемости университета
    def get_university_dynamic(self, start_date: date, end_date: date) -> List[AttendanceDailyDynamic]:
        return self._get_daily_dynamic(start_date, end_date)

    # 2. Получение динамики посещаемости группы
    def get_group_dynamic(self, group_id: int, start_date: date, end_date: date) -> List[AttendanceDailyDynamic]:
        return self._get_daily_dynamic(start_date, end_date, group_id)

    # 3. Кластеризация студентов группы
    def cluster_group_students(self, group_id: int, start_date: date, end_date: date) -> Dict[str, List[SendStudentCluster]]:
        students = self.db_class.getAllStudentsByGroup(group_id)
        cluster_data = {"Стабильные": [], "Рисковые": [], "Проблемные": []}
        for student in students:
            # Получаем все занятия студента за период
            attendances = (self.db_class.session.query(AttendanceDB)
                           .join(ScheduleDB, AttendanceDB.schedule_id == ScheduleDB.id)
                           .filter(ScheduleDB.group_id == group_id, ScheduleDB.date.between(start_date, end_date),
                                   AttendanceDB.student_id == student.id).all())
            total = len(attendances)
            attended = sum(1 for a in attendances if a.status)
            percent = (attended / total * 100) if total > 0 else 0
            # Определяем кластер
            if percent >= 80:
                cluster = "Стабильные"
            elif 50 <= percent < 80:
                cluster = "Рисковые"
            else:
                cluster = "Проблемные"
            cluster_data[cluster].append(
                SendStudentCluster(
                    student_id=student.id,
                    student_name=student.name,
                    attendance_percent=percent,
                    cluster=cluster
                )
            )
        return cluster_data

    # 4. Анализ по институтам
    def analyze_institutes_attendance(self, start_date: date, end_date: date) -> List[SendInstituteAnalysis]:
        institutes = self.db_class.getAllInstitutes()
        result = []
        for institute in institutes:
            total_possible = 0
            total_attended = 0
            # Получаем все группы института
            groups = self.db_class.getAllGroupsByInstitute(institute.id)
            for group in groups:
                # Считаем посещения для каждой группы
                schedules = self.db_class.getScheduleForGroup(group.id, start_date, end_date)
                for schedule in schedules:
                    students = self.db_class.getAllStudentsByGroup(group.id)
                    total_possible += len(students)
                    attendances = self.db_class.getAttendanceByScheduleId(schedule.id)
                    if attendances:
                        total_attended += sum(1 for a in attendances if a.status)
            percent = (total_attended / total_possible * 100) if total_possible > 0 else 0
            result.append(
                SendInstituteAnalysis(
                    institute_id=institute.id,
                    name=institute.name,
                    attendance_percent=percent
                )
            )
        return result

    # 5. Топ преподавателей по посещаемости
    def get_top_teachers_attendance(self, start_date: date, end_date: date) -> List[SendTeacherAttendance]:
        teachers = self.db_class.session.query(TeachersDB).all()
        results = []
        for teacher in teachers:
            total_possible = 0
            total_attended = 0
            # Получаем все занятия преподавателя за период
            schedules = self.db_class.getScheduleForTeacher(
                teacher.id, start_date, end_date
            )
            for schedule in schedules:
                students = self.db_class.getAllStudentsByGroup(schedule.group_id)
                if not students:
                    continue
                total_possible += len(students)
                attendances = self.db_class.getAttendanceByScheduleId(schedule.id)
                if attendances:
                    total_attended += sum(1 for a in attendances if a.status)
            attendance_percent = (total_attended / total_possible * 100) if total_possible > 0 else 0
            results.append(SendTeacherAttendance(
                teacher.id,
                teacher.name,
                attendance_percent,
                len(schedules)
            ))
        return sorted(results, key=lambda x: x.attendance_percent, reverse=True)[:10]

    # 6. Топ студентов по пропускам
    def get_top_students_absences(self, start_date: date, end_date: date) -> List[SendStudentAbsences]:
        absences = (self.db_class.session.query(
            StudentsDB.id,
            StudentsDB.name,
            GroupsDB.name,
            func.count(AttendanceDB.id)
        ).join(AttendanceDB, StudentsDB.id == AttendanceDB.student_id)
                    .join(ScheduleDB, AttendanceDB.schedule_id == ScheduleDB.id)
                    .join(GroupsDB, StudentsDB.group_id == GroupsDB.id)
                    .filter(ScheduleDB.date.between(start_date, end_date), AttendanceDB.status == False)
                    .group_by(StudentsDB.id, GroupsDB.name)
                    .order_by(func.count(AttendanceDB.id).desc()).limit(10).all())
        return [SendStudentAbsences(s[0], s[1], s[3], s[2]) for s in absences]

    # 7. Топ групп по пропускам
    def get_top_groups_absences(self, start_date: date, end_date: date) -> List[SendGroupAbsences]:
        absences = (self.db_class.session.query(
            GroupsDB.id,
            GroupsDB.name,
            func.count(AttendanceDB.id)
        ).join(StudentsDB, GroupsDB.id == StudentsDB.group_id)
                    .join(AttendanceDB, StudentsDB.id == AttendanceDB.student_id)
                    .join(ScheduleDB, AttendanceDB.schedule_id == ScheduleDB.id)
                    .filter(ScheduleDB.date.between(start_date, end_date), AttendanceDB.status == False)
                    .group_by(GroupsDB.id)
                    .order_by(func.count(AttendanceDB.id).desc()).limit(10).all())
        return [SendGroupAbsences(g[0], g[1], g[2]) for g in absences]

    # 8. Топ групп по посещаемости
    def get_top_groups_by_attendance(self, start_date: date, end_date: date) -> List[SendGroupAttendance]:
        groups = self.db_class.session.query(GroupsDB).all()
        group_attendance_list = []
        for group in groups:
            # Получаем все занятия группы за период
            schedules = self.db_class.getScheduleForGroup(
                group_id=group.id,
                week_start=start_date,
                week_end=end_date
            )
            total_possible = 0
            total_attended = 0
            for schedule in schedules:
                # Получаем студентов группы
                students = self.db_class.getAllStudentsByGroup(group.id)
                if not students:
                    continue
                num_students = len(students)
                total_possible += num_students
                # Считаем посещения для текущего занятия
                attendances = self.db_class.getAttendanceByScheduleId(schedule.id)
                if attendances:
                    attended = sum(1 for a in attendances if a.status)
                    total_attended += attended
            # Рассчитываем процент посещаемости
            attendance_percent = 0.0
            if total_possible > 0:
                attendance_percent = (total_attended / total_possible) * 100
            group_attendance_list.append(
                SendGroupAttendance(
                    group_id=group.id,
                    group_name=group.name,
                    attendance_percent=attendance_percent,
                    total_attendance=total_attended
                )
            )
        # Сортируем и выбираем топ-10
        sorted_groups = sorted(
            group_attendance_list,
            key=lambda x: x.attendance_percent,
            reverse=True
        )[:10]
        return sorted_groups
