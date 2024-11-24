from flask import Response, request
from source_code.resources.main_res import MainRes


class ScheduleDeviceRes(MainRes):
    # Получение расписания студента на текущую неделю по фото
    def post(self):
        device_id: int = int(request.form.get('device_id'))
        file = request.files.get('file')
        if file is None:
            return Response(response={"error": "No file"}, status=500)
        student_id, json_model, code = self.api_connector.getStudentScheduleByPhoto(file)
        if code == 0:
            self.app_metrica_reporter.sendEvent(event_name="DeviceScheduleStudent", event_json={
                "device_id": device_id,
                "student_id": student_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return self.__getErrorResponseByCode(code)

    @staticmethod
    def __getErrorResponseByCode(code) -> Response:
        if code == 1:
            return Response(response={"error: Не удалось декодировать изображение."}, status=501)
        elif code == 2:
            return Response(response={"error: Лицо не обнаружено на изображении."}, status=502)
        elif code == 3:
            return Response(response={"error: На изображении обнаружено несколько лиц."}, status=503)
        elif code == 4:
            return Response(response={"error: На изображении обнаружено неизвестное лицо."}, status=504)
        elif code == 5:
            return Response(response={"error: В системе не зарегистрирован ни один студент."}, status=507)
        elif code == 6:
            return Response(response={"error: Не найдены подходящие студенты."}, status=506)
        else:
            return Response(response={"error: Internal Server Error"}, status=500)
