from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminBuildingsRes(MainRes):
    # Получение всех корпусов
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        json_model = self.api_connector.getAllBuildings()
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminBuildingsGetAll", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        building_id: int = int(request.form.get('building_id'))

        json_model = self.api_connector.getBuilding(building_id=building_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserBuildingGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "building_id": building_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
