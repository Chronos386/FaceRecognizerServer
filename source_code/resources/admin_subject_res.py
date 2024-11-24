from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminSubjectRes(MainRes):
    # Получение всех предметов
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        json_model = self.api_connector.getAllSubjects()
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminSubjectsGetAll", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        subject_id: int = int(request.form.get('subject_id'))

        json_model = self.api_connector.getSubject(subject_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserSubjectGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "subject_id": subject_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
