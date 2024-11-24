from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminScheduleActionsRes(MainRes):
    # Создание нового пункта расписания
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        date = self.getDate()
        time_start, time_end = self.getTime()
        group_id: int = int(request.form.get('group_id'))
        subject_id: int = int(request.form.get('subject_id'))
        teacher_id: int = int(request.form.get('teacher_id'))
        room_id: int = int(request.form.get('room_id'))

        json_model = self.api_connector.createSchedule(date_schedule=date, time_start=time_start, time_end=time_end,
                                                       group_id=group_id, subject_id=subject_id, teacher_id=teacher_id,
                                                       room_id=room_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewSchedule", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "group_id": group_id,
                "subject_id": subject_id,
                "teacher_id": teacher_id,
                "room_id": room_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление пункта расписания
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        schedule_id: int = int(request.form.get('schedule_id'))
        date = self.getDate()
        time_start, time_end = self.getTime()
        group_id: int = int(request.form.get('group_id'))
        subject_id: int = int(request.form.get('subject_id'))
        teacher_id: int = int(request.form.get('teacher_id'))
        room_id: int = int(request.form.get('room_id'))

        json_model = self.api_connector.updateSchedule(date_schedule=date, time_start=time_start, time_end=time_end,
                                                       schedule_id=schedule_id, group_id=group_id, room_id=room_id,
                                                       subject_id=subject_id, teacher_id=teacher_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateSchedule", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "schedule_id": schedule_id,
                "group_id": group_id,
                "subject_id": subject_id,
                "teacher_id": teacher_id,
                "room_id": room_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление пункта расписания
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        schedule_id: int = int(request.form.get('schedule_id'))
        code = self.api_connector.deleteSchedule(schedule_id=schedule_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteSchedule", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "schedule_id": schedule_id,
        })
        return Response(status=code)
