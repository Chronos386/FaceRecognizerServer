from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminBuildingActionsRes(MainRes):
    # Создание нового корпуса
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        name: str = request.form.get('name')
        address: str = request.form.get('address')
        json_model = self.api_connector.createBuilding(name=name, address=address)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewBuilding", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление корпуса
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        building_id: int = int(request.form.get('building_id'))
        name: str = request.form.get('name')
        address: str = request.form.get('address')
        json_model = self.api_connector.updateBuilding(building_id=building_id, name=name, address=address)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateBuilding", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "address": address,
                "building_id": building_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующего корпуса
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        building_id: int = int(request.form.get('building_id'))
        code = self.api_connector.deleteBuilding(building_id=building_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteBuilding", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "building_id": building_id,
        })
        return Response(status=code)
