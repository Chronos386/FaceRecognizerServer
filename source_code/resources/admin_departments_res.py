from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminDepartmentsRes(MainRes):
    # Получение всех кафедр института
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        id_institute: int = int(request.form.get('id_institute'))

        json_model = self.api_connector.getAllDepartmentsByInstitute(id_institute)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminDepartmentsGetAll", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "id_institute": id_institute,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        department_id: int = int(request.form.get('department_id'))

        json_model = self.api_connector.getDepartment(department_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserDepartmentGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "department_id": department_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
