import json
import time
import requests
import threading
from source_code.utils.logger_file import logger


class AppMetricaReporter:
    def __init__(self):
        self.post_api_key = "09c5118e-49a4-4703-af8b-460157a13cfb"
        self.application_id = 4649854
        self.appmetrica_device_id = 14766913885733900580
        self.url = "https://api.appmetrica.yandex.ru/logs/v1/import/events"

    def __send_event_worker(self, event_name: str, event_json: dict):
        event_timestamp = int(time.time())
        params = {
            "post_api_key": self.post_api_key,
            "application_id": self.application_id,
            "appmetrica_device_id": self.appmetrica_device_id,
            "event_name": event_name,
            "event_timestamp": event_timestamp,
            "event_json": json.dumps(event_json, ensure_ascii=False),
            "session_type": "foreground"
        }
        try:
            response = requests.post(self.url, params=params)
            if response.status_code != 200:
                logger.error(f"Ошибка при отправке события: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке события: {e}")

    def sendEvent(self, event_name: str, event_json: dict):
        thread = threading.Thread(target=self.__send_event_worker, args=(event_name, event_json), daemon=True)
        thread.start()
