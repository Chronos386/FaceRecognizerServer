from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminScheduleTeacherRes(MainRes):
    # Получение админом расписания преподавателя на неделю
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        teacher_id: int = int(request.form.get('teacher_id'))
        dates = self.getDates()
        if dates is None:
            return Response(response={"error": "Wrong date format"}, status=500)

        json_model = self.api_connector.getTeacherScheduleByTeacherId(teacher_id, dates[0], dates[1])
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminScheduleTeacher", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "teacher_id": teacher_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
