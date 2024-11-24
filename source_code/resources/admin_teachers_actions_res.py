from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminTeachersActionsRes(MainRes):
    # Создание нового преподавателя
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')
        email: str = request.form.get('email')
        password: str = request.form.get('password')
        department_id: int = int(request.form.get('department_id'))

        json_model = self.api_connector.createTeacher(name, email, password, department_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewTeacher", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "email": email,
                "password": password,
                "department_id": department_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление преподавателя
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')
        id_teacher: int = int(request.form.get('id_teacher'))
        department_id: int = int(request.form.get('department_id'))

        json_model = self.api_connector.updateTeacher(id_teacher, name, department_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateTeacher", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "id_teacher": id_teacher,
                "name": name,
                "department_id": department_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующего преподавателя
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        id_teacher: int = int(request.form.get('id_teacher'))

        code = self.api_connector.deleteTeacher(id_teacher=id_teacher)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteTeacher", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "id_teacher": id_teacher,
        })
        return Response(status=code)
