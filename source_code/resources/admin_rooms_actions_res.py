from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminRoomsActionsRes(MainRes):
    # Создание новой комнаты
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        number: str = request.form.get('number')
        building_id: int = int(request.form.get('building_id'))

        json_model = self.api_connector.createRoom(building_id=building_id, number=number)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewRoom", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "number": number,
                "building_id": building_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление комнаты
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        room_id: int = int(request.form.get('room_id'))
        building_id: int = int(request.form.get('building_id'))
        number: str = request.form.get('number')

        json_model = self.api_connector.updateRoom(building_id=building_id, number=number, room_id=room_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateRoom", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "room_id": room_id,
                "number": number,
                "building_id": building_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующей комнаты
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        room_id: int = int(request.form.get('room_id'))

        code = self.api_connector.deleteRoom(room_id=room_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteRoom", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "room_id": room_id,
        })
        return Response(status=code)
