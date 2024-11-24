from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminGroupsRes(MainRes):
    # Получение всех групп института
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        institute_id: int = int(request.form.get('institute_id'))

        json_model = self.api_connector.getAllGroupsByInstitute(institute_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminGroupsGetAll", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "institute_id": institute_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        group_id: int = int(request.form.get('group_id'))

        json_model = self.api_connector.getGroup(group_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="UserGroupsGet", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
                "group_id": group_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)
