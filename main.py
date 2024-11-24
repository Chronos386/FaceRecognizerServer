import os
import atexit
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
from source_code.resources.admin_rooms_actions_res import AdminRoomsActionsRes
from source_code.resources.admin_schedule_group_res import AdminScheduleGroupRes
from source_code.resources.admin_device_actions_res import AdminDeviceActionsRes
from source_code.resources.admin_groups_actions_res import AdminGroupsActionsRes
from source_code.resources.admin_subject_actions_res import AdminSubjectActionsRes
from source_code.resources.admin_schedule_actions_res import AdminScheduleActionsRes
from source_code.resources.admin_schedule_teacher_res import AdminScheduleTeacherRes
from source_code.resources.admin_teachers_actions_res import AdminTeachersActionsRes
from source_code.resources.admin_students_actions_res import AdminStudentsActionsRes
from source_code.resources.admin_buildings_actions_res import AdminBuildingActionsRes
from source_code.resources.attendance_group_teacher_res import AttendanceGroupTeacherRes
from source_code.resources.admin_institutes_actions_res import AdminInstitutesActionsRes
from source_code.resources.admin_departments_actions_res import AdminDepartmentsActionsRes

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
    # application.run(host='0.0.0.0', port=80, debug=False)
    serve(application, host="0.0.0.0", port=80)
