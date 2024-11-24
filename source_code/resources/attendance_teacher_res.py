from flask import Response, request
from source_code.resources.main_res import MainRes


class AttendanceTeacherRes(MainRes):
    # Изменение статуса посещаемости студента
    def post(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        student_id: int = int(request.form.get('student_id'))
        schedule_id: int = int(request.form.get('schedule_id'))
        status: bool = (request.form.get('status') == "true")

        code = self.api_connector.martAttendanceByTeacher(acc_id, student_id, schedule_id, status)
        if code == 200:
            self.app_metrica_reporter.sendEvent(event_name="ChangeStudentAttendance", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "student_id": student_id,
                "schedule_id": schedule_id,
                "status": status,
            })
        return Response(status=code)
