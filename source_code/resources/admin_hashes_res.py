from flask import Response, request
from source_code.resources.main_res import MainRes


class AdminHashesRes(MainRes):
    def delete(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response
        self.api_connector.deleteAllHashes()
        self.app_metrica_reporter.sendEvent(event_name="AdminDeleteAllHashes", event_json={
            "hash": hash_admin,
            "acc_id": acc_id,
        })
        return Response(status=200)
