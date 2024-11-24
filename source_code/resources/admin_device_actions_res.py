from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminDeviceActionsRes(MainRes):
    # Создание нового девайса
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        room_id: int = int(request.form.get('room_id'))
        json_model = self.api_connector.createDevice(room_id=room_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewDevice", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "room_id": room_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление девайса
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        device_id: int = int(request.form.get('device_id'))
        code = self.api_connector.deleteDevice(device_id=device_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteDevice", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "device_id": device_id,
        })
        return Response(status=code)
