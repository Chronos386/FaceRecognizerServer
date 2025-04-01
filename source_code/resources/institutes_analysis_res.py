# institutes_analysis_res.py
from flask import Response, request
from source_code.resources.main_res import MainRes

class InstitutesAnalysisRes(MainRes):
    def post(self):
        hash_admin = request.form.get('hash')
        acc_id, error = self.check_admin_access(hash_admin)
        if error:
            return error
        dates = self.getDates()
        if not dates:
            return Response(response={"error": "Invalid date format"}, status=400)
        json_model = self.api_connector.getInstitutesAnalysis(dates[0], dates[1])
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="InstitutesAnalysis", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(response={"error": "Database error"}, status=500)