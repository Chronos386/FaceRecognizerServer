from flask import Response, request
from source_code.resources.main_res import MainRes


class StudentsRes(MainRes):
    # Получение списка группы
    def post(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        group_id: int = int(request.form.get('group_id'))

        json_model = self.api_connector.getAllStudentsByGroup(group_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="GroupGetMembers", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "group_id": group_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        student_id: int = int(request.form.get('student_id'))

        json_model = self.api_connector.getStudent(student_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserStudentGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "student_id": student_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
