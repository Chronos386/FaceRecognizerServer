from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminInstitutesActionsRes(MainRes):
    # Создание нового института
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        name: str = request.form.get('name')
        json_model = self.api_connector.createInstitute(name=name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewInstitute", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление института
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        id_institute: int = int(request.form.get('id_institute'))
        name: str = request.form.get('name')
        json_model = self.api_connector.updateInstitute(id_institute=id_institute, name=name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateInstitute", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "id_institute": id_institute,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующего института
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        id_institute: int = int(request.form.get('id_institute'))
        code = self.api_connector.deleteInstitute(id_institute=id_institute)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteInstitute", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "id_institute": id_institute,
        })
        return Response(status=code)
