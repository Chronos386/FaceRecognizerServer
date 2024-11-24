from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminGroupsActionsRes(MainRes):
    # Создание новой группы
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        name: str = request.form.get('name')
        institute_id: int = int(request.form.get('institute_id'))

        json_model = self.api_connector.createGroup(institute_id, name)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminNewGroup", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "name": name,
                "institute_id": institute_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Обновление группы
    def put(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        group_id: int = int(request.form.get('group_id'))
        institute_id: int = int(request.form.get('institute_id'))
        name: str = request.form.get('name')

        json_model = self.api_connector.updateGroup(group_id=group_id, name=name, id_institute=institute_id)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="AdminUpdateGroup", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "group_id": group_id,
                "name": name,
                "institute_id": institute_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)

    # Удаление существующей группы
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        group_id: int = int(request.form.get('group_id'))

        code = self.api_connector.deleteGroup(group_id=group_id)
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteGroup", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
            "group_id": group_id,
        })
        return Response(status=code)
