from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminTeachersRes(MainRes):
    # Получение всех преподавателей кафедры
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        department_id: int = int(request.form.get('department_id'))

        json_model = self.api_connector.getAllTeachersByDepartment(department_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminTeachersGetAll", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "department_id": department_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        teacher_id: int = int(request.form.get('teacher_id'))

        json_model = self.api_connector.getTeacher(teacher_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserTeacherGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "teacher_id": teacher_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
