import os
import atexit
'''
from faker import Faker
from transliterate import translit  # Установите: pip install transliterate
from datetime import date, time, timedelta
import random
from source_code.db_connection.db_models.rooms_db import RoomsDB
from source_code.db_connection.db_models.schedule_db import ScheduleDB
'''
import werkzeug.exceptions
from waitress import serve
from flask_cors import CORS
from flask_restful import Api
from werkzeug.utils import secure_filename
from source_code.utils.logger_file import logger
from source_code.di.di_container import DiContainer
from source_code.db_connection.db_class import DBClass
from dependency_injector.wiring import inject, Provide
from source_code.resources.user_acc_res import UserAccRes
from source_code.resources.students_res import StudentsRes
from source_code.resources.admin_rooms_res import AdminRoomsRes
from source_code.resources.admin_hashes_res import AdminHashesRes
from apscheduler.schedulers.background import BackgroundScheduler
from source_code.api_connection.api_connector import ApiConnector
from source_code.resources.admin_groups_res import AdminGroupsRes
from source_code.resources.admin_subject_res import AdminSubjectRes
from source_code.resources.admin_teachers_res import AdminTeachersRes
from source_code.resources.group_clusters_res import GroupClustersRes
from source_code.resources.schedule_device_res import ScheduleDeviceRes
from source_code.resources.admin_buildings_res import AdminBuildingsRes
from flask import Flask, send_file, request, url_for, redirect, Response
from source_code.resources.schedule_teacher_res import ScheduleTeacherRes
from source_code.resources.schedule_student_res import ScheduleStudentRes
from source_code.resources.admin_institutes_res import AdminInstitutesRes
from source_code.resources.admin_embeddings_res import AdminEmbeddingsRes
from source_code.resources.admin_departments_res import AdminDepartmentsRes
from source_code.resources.attendance_device_res import AttendanceDeviceRes
from source_code.resources.attendance_teacher_res import AttendanceTeacherRes
from source_code.resources.attendance_student_res import AttendanceStudentRes
from source_code.resources.top_groups_absences_res import TopGroupsAbsencesRes
from source_code.resources.admin_rooms_actions_res import AdminRoomsActionsRes
from source_code.resources.institutes_analysis_res import InstitutesAnalysisRes
from source_code.resources.admin_schedule_group_res import AdminScheduleGroupRes
from source_code.resources.admin_device_actions_res import AdminDeviceActionsRes
from source_code.resources.admin_groups_actions_res import AdminGroupsActionsRes
from source_code.resources.top_groups_attendance_res import TopGroupsAttendanceRes
from source_code.resources.top_students_absences_res import TopStudentsAbsencesRes
from source_code.resources.admin_subject_actions_res import AdminSubjectActionsRes
from source_code.resources.admin_schedule_actions_res import AdminScheduleActionsRes
from source_code.resources.admin_schedule_teacher_res import AdminScheduleTeacherRes
from source_code.resources.admin_teachers_actions_res import AdminTeachersActionsRes
from source_code.resources.admin_students_actions_res import AdminStudentsActionsRes
from source_code.resources.admin_buildings_actions_res import AdminBuildingActionsRes
from source_code.resources.top_teachers_attendance_res import TopTeachersAttendanceRes
from source_code.resources.group_attendance_dynamic_res import GroupAttendanceDynamicRes
from source_code.resources.attendance_group_teacher_res import AttendanceGroupTeacherRes
from source_code.resources.admin_institutes_actions_res import AdminInstitutesActionsRes
from source_code.resources.admin_departments_actions_res import AdminDepartmentsActionsRes
from source_code.resources.university_attendance_dynamic_res import UniversityAttendanceDynamicRes

#  Настройка сервера
application = Flask(__name__)
pictures_folder = 'files/pictures'
application.config['SESSION_TYPE'] = 'filesystem'
application.config['PROPAGATE_EXCEPTIONS'] = True
application.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000
application.secret_key = 'server_facial_recognition_for_automatic_student_attendance_marking_key'
application.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), pictures_folder)
api = Api()
CORS(application)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
api.add_resource(UserAccRes, "/api/user/account/")

api.add_resource(UniversityAttendanceDynamicRes, '/api/stats/university-attendance/')
api.add_resource(GroupAttendanceDynamicRes, '/api/stats/group-attendance/')
api.add_resource(GroupClustersRes, '/api/stats/group-clusters/')
api.add_resource(InstitutesAnalysisRes, '/api/stats/institutes-analysis/')
api.add_resource(TopTeachersAttendanceRes, '/api/stats/top-teachers/')
api.add_resource(TopStudentsAbsencesRes, '/api/stats/top-students-absences/')
api.add_resource(TopGroupsAbsencesRes, '/api/stats/top-groups-absences/')
api.add_resource(TopGroupsAttendanceRes, '/api/stats/top-groups-attendance/')

api.add_resource(ScheduleDeviceRes, "/api/device/schedule/")
api.add_resource(ScheduleStudentRes, "/api/user/student/schedule/")
api.add_resource(ScheduleTeacherRes, "/api/user/teacher/schedule/")
api.add_resource(AdminScheduleGroupRes, "/api/admin/group/schedule/")
api.add_resource(AdminScheduleTeacherRes, "/api/admin/teacher/schedule/")

api.add_resource(AdminHashesRes, "/api/admin/hashes/")
api.add_resource(AdminEmbeddingsRes, "/api/admin/embeddings/")
api.add_resource(StudentsRes, "/api/user/student/")
api.add_resource(AdminStudentsActionsRes, "/api/admin/student/actions/")
api.add_resource(AdminInstitutesRes, "/api/admin/institute/")
api.add_resource(AdminInstitutesActionsRes, "/api/admin/institute/actions/")
api.add_resource(AdminDepartmentsRes, "/api/admin/department/")
api.add_resource(AdminDepartmentsActionsRes, "/api/admin/department/actions/")
api.add_resource(AdminTeachersRes, "/api/admin/teacher/")
api.add_resource(AdminTeachersActionsRes, "/api/admin/teacher/actions/")
api.add_resource(AdminGroupsRes, "/api/admin/group/")
api.add_resource(AdminGroupsActionsRes, "/api/admin/group/actions/")
api.add_resource(AdminSubjectRes, "/api/admin/subject/")
api.add_resource(AdminSubjectActionsRes, "/api/admin/subject/actions/")
api.add_resource(AdminBuildingsRes, "/api/admin/building/")
api.add_resource(AdminBuildingActionsRes, "/api/admin/building/actions/")
api.add_resource(AdminRoomsRes, "/api/admin/room/")
api.add_resource(AdminRoomsActionsRes, "/api/admin/room/actions/")
api.add_resource(AdminScheduleActionsRes, "/api/admin/schedule/actions/")
api.add_resource(AdminDeviceActionsRes, "/api/admin/device/actions/")

api.add_resource(AttendanceDeviceRes, "/api/device/attendance/")
api.add_resource(AttendanceTeacherRes, "/api/teacher/attendance/")
api.add_resource(AttendanceGroupTeacherRes, "/api/teacher/group/attendance/")
api.add_resource(AttendanceStudentRes, "/api/student/attendance/")
api.init_app(app=application)
container = DiContainer()

# Настройка автоматической очистки старых хэшей
@inject
def deleteOldHashesJob(db_class: DBClass = Provide[DiContainer.db_class]):
    db_class.deleteOldHashes()

'''
fake = Faker('ru_RU')
@inject
def generate_students(db_class: DBClass = Provide[DiContainer.db_class]):
    groups = db_class.getAllGroups()  # Получаем все существующие группы
    for _ in range(150):
        ru_name = fake.name()
        username = translit(ru_name.split()[0], 'ru', reversed=True).lower()
        email = f"{username}.{fake.random_int(100, 999)}@bsuedu.ru"
        # Создаем аккаунт
        acc = db_class.createAccount(email=email, password="student_password")
        # Выбираем случайную группу
        group = fake.random_element(groups)
        # Создаем студента
        db_class.createStudent(
            name=ru_name,
            acc_id=acc.id,
            group_id=group.id
        )

@inject
def generate_schedule(db: DBClass = Provide[DiContainer.db_class]):
    # Даты с 17 по 30 марта 2025 (исключая субботы и воскресенья)
    start_date = date(2025, 3, 17)
    end_date = date(2025, 3, 30)
    excluded_dates = [date(2025, 3, 22), date(2025, 3, 23), date(2025, 3, 29), date(2025, 3, 30)]

    # Временные слоты для занятий
    time_slots = [
        (time(9, 0), time(10, 30)),
        (time(11, 0), time(12, 30)),
        (time(14, 0), time(15, 30)),
        (time(16, 0), time(17, 30)),
        (time(18, 0), time(19, 30)),
        (time(20, 0), time(21, 30))
    ]

    # Получаем данные из БД
    groups = db.getAllGroups()
    subjects = db.getAllSubjects()
    rooms = db.session.query(RoomsDB).all()

    current_date = start_date
    while current_date <= end_date:
        if current_date in excluded_dates or current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        for group in groups:
            # Получаем институт группы
            institute_id = group.institute_id

            # Получаем преподавателей института
            departments = db.getAllDepartmentsByInstitute(institute_id)
            teachers = []
            for dep in departments:
                teachers.extend(db.getAllTeachersByDepartment(dep.id))

            for slot in time_slots:
                time_start, time_end = slot

                # Проверка занятости группы
                group_busy = db.session.query(ScheduleDB).filter(
                    ScheduleDB.group_id == group.id,
                    ScheduleDB.date == current_date,
                    ScheduleDB.time_start < time_end,
                    ScheduleDB.time_end > time_start
                ).first()
                if group_busy:
                    continue

                # Выбираем случайные параметры
                subject = random.choice(subjects)
                teacher = random.choice(teachers) if teachers else None
                if not teacher:
                    continue

                # Проверка занятости преподавателя
                teacher_busy = db.session.query(ScheduleDB).filter(
                    ScheduleDB.teacher_id == teacher.id,
                    ScheduleDB.date == current_date,
                    ScheduleDB.time_start < time_end,
                    ScheduleDB.time_end > time_start
                ).first()
                if teacher_busy:
                    continue

                # Поиск свободной аудитории
                for room in random.sample(rooms, len(rooms)):
                    room_busy = db.session.query(ScheduleDB).filter(
                        ScheduleDB.room_id == room.id,
                        ScheduleDB.date == current_date,
                        ScheduleDB.time_start < time_end,
                        ScheduleDB.time_end > time_start
                    ).first()
                    if not room_busy:
                        db.createSchedule(
                            date_schedule=current_date,
                            time_start=time_start,
                            time_end=time_end,
                            group_id=group.id,
                            subject_id=subject.id,
                            teacher_id=teacher.id,
                            room_id=room.id
                        )
                        break

        current_date += timedelta(days=1)


# Глобальный кэш для кластеров студентов
student_clusters = {}


def determine_cluster(student_id: int) -> str:
    """Определяет кластер студента с вероятностями:
    - Стабильные (80-100%): 60%
    - Рисковые (50-80%): 30%
    - Проблемные (<50%): 10%
    """
    if student_id in student_clusters:
        return student_clusters[student_id]

    rand = random.random()
    if rand <= 0.6:
        cluster = 'stable'
    elif rand <= 0.9:
        cluster = 'risky'
    else:
        cluster = 'problematic'

    student_clusters[student_id] = cluster
    return cluster


@inject
def mark_attendance(db: DBClass = Provide[DiContainer.db_class]):
    # Даты периода (17-30 марта 2025, исключая выходные)
    start_date = date(2025, 3, 17)
    end_date = date(2025, 3, 30)
    excluded_dates = [
        date(2025, 3, 22), date(2025, 3, 23),  # Суббота и воскресенье
        date(2025, 3, 29), date(2025, 3, 30)  # Суббота и воскресенье
    ]

    # Получаем все расписания
    all_schedules = []
    for group in db.getAllGroups():
        schedules = db.getScheduleForGroup(group.id, start_date, end_date)
        all_schedules.extend(schedules)

    # Обработка каждого занятия
    for schedule in all_schedules:
        if schedule.date in excluded_dates or schedule.date.weekday() >= 5:
            continue

        # Динамический фактор дня (пример: пятница -10%)
        day_factor = 1.0
        if schedule.date.weekday() == 4:  # Пятница
            day_factor = 0.9

        students = db.getAllStudentsByGroup(schedule.group_id)
        for student in students:
            cluster = determine_cluster(student.id)

            # Базовые вероятности по кластерам
            if cluster == 'stable':
                base_prob = random.uniform(0.85, 0.95)  # 85-95%
            elif cluster == 'risky':
                base_prob = random.uniform(0.6, 0.75)  # 60-75%
            else:
                base_prob = random.uniform(0.3, 0.5)  # 30-50%

            # Корректировка с учетом дня и случайного шума
            final_prob = base_prob * day_factor
            final_prob += random.uniform(-0.05, 0.05)  # ±5% шума
            final_prob = max(0.25, min(final_prob, 0.95))  # Границы [25%, 95%]

            status = random.random() < final_prob

            # Обновление или создание записи
            existing = db.getStudentAttendanceByScheduleId(student.id, schedule.id)
            if existing:
                db.markAttendance(student.id, schedule.id, status)
            else:
                db.markAttendance(student.id, schedule.id, status)
'''

# Отметить отсутствие студентов на занятии
@inject
def markAbsenceAttendance(api_connector: ApiConnector = Provide[DiContainer.api_connector]):
    api_connector.markAbsenceAttendance()


#  Функции сервера
def allowedFile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#  Отлавливание всех ошибок
@application.errorhandler(Exception)
def handleException(e):
    logger.error(f"Необработанная ошибка: {e}", exc_info=True)
    if isinstance(e, werkzeug.exceptions.NotFound):
        return redirect(url_for('index'))
    return Response(response={"message": "Internal Server Error"}, status=500)


#  Начальная страница
@application.route("/")
def index():
    return send_file('files/index.html')


#  Иконка сайта
@application.route('/favicon.ico')
def favicon():
    return send_file(f'{pictures_folder}/favicon.ico')


#  Загрузка фото на сервер
@application.route('/api/pictures/', methods=['POST'])
def downloadPict():
    if 'file' not in request.files:
        return Response(response={"error": "No file"}, status=500)
    file = request.files['file']
    if file.filename == '':
        return Response(response={"error": "No file name"}, status=500)
    if file and allowedFile(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        return Response(status=200)


#  Получение фото с сервера
@application.route('/pictures/<string:pict_name>', methods=['GET'])
def loadPict(pict_name: str):
    filename = f"{pictures_folder}/{pict_name}"
    parts = pict_name.split(".")
    try:
        return send_file(filename, mimetype=f'image/{parts[1]}')
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return handleException(werkzeug.exceptions.NotFound())


if __name__ == '__main__':
    # Регистрируем функции для очистки старых хэшей раз в сутки и отметки отсутствия студентов на занятии раз в час
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=deleteOldHashesJob, trigger="interval", days=1)
    scheduler.add_job(func=markAbsenceAttendance, trigger="interval", hours=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    # Регистрируем ресурсы для DI
    container.wire(modules=[__name__, 'source_code.resources.main_res'])

    # Запуск сервера
    # application.run(host='127.0.0.1', port=80, debug=False) host="172.20.10.13", port=6583
    serve(application, host='127.0.0.1', port=6583, threads=8)
