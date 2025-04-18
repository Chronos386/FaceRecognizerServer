from flask import Response, request
from source_code.resources.main_res import MainRes

class AttendanceGroupTeacherRes(MainRes):
    # Получение посещаемости группы по schedule_id
    def post(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_user)
        if error_response:
            return error_response

        schedule_id: int = int(request.form.get('schedule_id'))
        code, json_model = self.api_connector.getAttendanceGroupBySchedule(schedule_id)
        if code == 200:
            self.app_metrica_reporter.sendEvent(event_name="TeacherAttendanceGroup", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "schedule_id": schedule_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(status=code)
