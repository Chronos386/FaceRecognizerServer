from flask import Response, request
from source_code.resources.main_res import MainRes


class ScheduleTeacherRes(MainRes):
    # Получение расписания преподавателя на неделю
    def post(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        dates = self.getDates()
        if dates is None:
            return Response(response={"error": "Wrong date format"}, status=500)

        json_model = self.api_connector.getTeacherScheduleByHash(acc_id, dates[0], dates[1])
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="TeacherSchedule", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
