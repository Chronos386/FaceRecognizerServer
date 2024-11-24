from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminDepartmentsActionsRes(MainRes):
    # Создание новой кафедры
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')
        id_institute: int = int(request.form.get('id_institute'))

        json_model = self.api_connector.createDepartment(id_institute, name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewDepartment", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "id_institute": id_institute,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление кафедры
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        id_department: int = int(request.form.get('id_department'))
        id_institute: int = int(request.form.get('id_institute'))
        name: str = request.form.get('name')

        json_model = self.api_connector.updateDepartment(id_department=id_department, id_institute=id_institute,
                                                         name=name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateDepartment", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "id_department": id_department,
                "name": name,
                "id_institute": id_institute,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующей кафедры
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        id_department: int = int(request.form.get('id_department'))
        code = self.api_connector.deleteDepartment(id_department=id_department)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteDepartment", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "id_department": id_department,
        })
        return Response(status=code)
