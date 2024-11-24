from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminSubjectActionsRes(MainRes):
    # Создание нового предмета
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')

        json_model = self.api_connector.createSubject(name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewSubject", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление предмета
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        subject_id: int = int(request.form.get('subject_id'))
        name: str = request.form.get('name')

        json_model = self.api_connector.updateSubject(subject_id=subject_id, name=name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateSubject", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "subject_id": subject_id,
                "name": name,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление предмета
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        subject_id: int = int(request.form.get('subject_id'))

        code = self.api_connector.deleteSubject(subject_id=subject_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteSubject", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "subject_id": subject_id,
        })
        return Response(status=code)
