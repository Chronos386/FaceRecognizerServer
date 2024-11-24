from flask import Response, request
from source_code.resources.main_res import MainRes


class AttendanceDeviceRes(MainRes):
    # Отметка посещаемости студента на паре по фото
    def post(self):
        device_id: int = int(request.form.get('device_id'))
        current_datetime = self.getDateTime()
        if current_datetime is None:
            return Response(response={"error": "Wrong datetime format"}, status=500)

        file = request.files.get('file')
        if file is None:
            return Response(response={"error": "No file"}, status=500)

        code, student_id, schedule_id, json_model = self.api_connector.markAttendanceByPhoto(
            file, current_datetime, device_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="DeviceAttendanceStudent", event_json={
                "device_id": device_id,
                "student_id": student_id,
                "schedule_id": schedule_id,
            })
            return Response(json_model, mimetype='application/json')
        if code > 100:
            return Response(status=code)
        else:
            return self.__getErrorResponseByCode(code)

    def delete(self):
        device_id: int = int(request.form.get('device_id'))
        student_id: int = int(request.form.get('student_id'))
        schedule_id: int = int(request.form.get('schedule_id'))

        code = self.api_connector.cancelMarkAttendanceByPhoto(student_id, schedule_id, device_id)
        return Response(status=code)

    @staticmethod
    def __getErrorResponseByCode(code) -> Response:
        if code == 1:
            return Response(response={"error": "Не удалось декодировать изображение."}, status=501)
        elif code == 2:
            return Response(response={"error": "Лицо не обнаружено на изображении."}, status=502)
        elif code == 3:
            return Response(response={"error": "На изображении обнаружено несколько лиц."}, status=503)
        elif code == 4:
            return Response(response={"error": "На изображении обнаружено неизвестное лицо."}, status=504)
        elif code == 5:
            return Response(response={"error": "В системе не зарегистрирован ни один студент."}, status=507)
        elif code == 6:
            return Response(response={"error": "Не найдены подходящие студенты."}, status=506)
        else:
            return Response(response={"error": "Internal Server Error"}, status=500)
