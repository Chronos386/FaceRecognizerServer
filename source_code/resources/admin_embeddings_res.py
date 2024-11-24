import json
from typing import List
from flask import Response, request, jsonify
from werkzeug.datastructures import FileStorage
from source_code.resources.main_res import MainRes


class AdminEmbeddingsRes(MainRes):
    # Получение всех корпусов
    def post(self):
        hash_admin: str = request.form.get('hash')
        acc_id, error_response = self.check_admin_access(hash_admin)
        if error_response:
            return error_response

        student_id: int = int(request.form.get('student_id'))
        photos: List[FileStorage] = request.files.getlist('photos')
        if not photos or len(photos) == 0:
            return Response(response={"error": "Отсутствуют файлы photos в запросе."}, status=400)

        codes = []
        for photo in photos:
            code = self.api_connector.createEmbedding(student_id=student_id, photo=photo)
            codes.append(code)
        json_data = json.dumps({'codes': codes})
        if json_data:
            self.app_metrica_reporter.sendEvent(event_name="AdminAddEmbeddings", event_json={
                "hash": hash_admin,
                "acc_id": acc_id,
                "student_id": student_id,
            })
            return Response(json_data, mimetype='application/json', status=200)
        else:
            return Response(response={"error": "Database error"}, status=500)
