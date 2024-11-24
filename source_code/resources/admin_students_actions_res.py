from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminStudentsActionsRes(MainRes):
    # Создание нового студента
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')
        email: str = request.form.get('email')
        password: str = request.form.get('password')
        group_id: int = int(request.form.get('group_id'))

        json_model = self.api_connector.createStudent(name, email, password, group_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewStudent", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "email": email,
                "password": password,
                "group_id": group_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление студента
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        student_id: int = int(request.form.get('student_id'))
        group_id: int = int(request.form.get('group_id'))
        name: str = request.form.get('name')

        json_model = self.api_connector.updateStudent(student_id=student_id, group_id=group_id, name=name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateStudent", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "student_id": student_id,
                "group_id": group_id,
                "name": name,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление студента
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        student_id: int = int(request.form.get('student_id'))

        code = self.api_connector.deleteStudent(student_id=student_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteGroup", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "student_id": student_id,
        })
        return Response(status=code)
