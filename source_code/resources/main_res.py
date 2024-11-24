from datetime import datetime, date, time
from typing import Optional, Tuple
from flask_restful import Resource
from flask import Response, request
from source_code.di.di_container import DiContainer
from dependency_injector.wiring import inject, Provide
from source_code.api_connection.api_connector import ApiConnector
from source_code.utils.app_metrica_reporter import AppMetricaReporter


class MainRes(Resource):
    @inject
    def __init__(self, api_connector: ApiConnector = Provide[DiContainer.api_connector],
                 app_metrica_reporter: AppMetricaReporter = Provide[DiContainer.app_metrica_reporter]):
        self.api_connector: ApiConnector = api_connector
        self.app_metrica_reporter: AppMetricaReporter = app_metrica_reporter

    def check_admin_access(self, hash_admin: str) -> Tuple[Optional[int], Optional[Response]]:
        acc_id: Optional[int] = self.api_connector.getAccIdByHash(hash_admin)
        if acc_id is None:
            return None, Response(status=401)

        is_admin: Optional[bool] = self.api_connector.checkIsAdminByHash(hash_admin)
        if is_admin is None:
            return None, Response(status=401)
        elif not is_admin:
            return None, Response(status=403)

        return acc_id, None

    def check_user_access(self, hash_admin: str) -> Tuple[Optional[int], Optional[Response]]:
        acc_id: Optional[int] = self.api_connector.getAccIdByHash(hash_admin)
        if acc_id is None:
            return None, Response(status=401)
        return acc_id, None

    @staticmethod
    def getDates() -> Optional[Tuple[date, date]]:
        date_start_str: str = request.form.get('date_start')
        date_end_str: str = request.form.get('date_end')
        try:
            date_start = datetime.fromisoformat(date_start_str).date()
            date_end = datetime.fromisoformat(date_end_str).date()
            return date_start, date_end
        except ValueError:
            return None

    @staticmethod
    def getDateTime() -> Optional[datetime]:
        datetime_str: str = request.form.get('datetime')
        try:
            current_datetime = datetime.fromisoformat(datetime_str)
            return current_datetime
        except ValueError:
            return None

    @staticmethod
    def getDate() -> Optional[date]:
        datetime_str: str = request.form.get('date')
        try:
            current_datetime = datetime.fromisoformat(datetime_str)
            return current_datetime.date()
        except ValueError:
            return None

    @staticmethod
    def getTime() -> Optional[Tuple[time, time]]:
        time_start_str: str = request.form.get('time_start')
        time_end_str: str = request.form.get('time_end')
        try:
            time_start = datetime.strptime(time_start_str, "%H:%M").time()
            time_end = datetime.strptime(time_end_str, "%H:%M").time()
            return time_start, time_end
        except ValueError:
            return None
