from dependency_injector import containers, providers
from source_code.db_connection.db_class import DBClass
from source_code.api_connection.api_connector import ApiConnector
from source_code.utils.app_metrica_reporter import AppMetricaReporter
from source_code.face_recognition.face_recognizer import FaceRecognizer


class DiContainer(containers.DeclarativeContainer):
    db_class = providers.Singleton(DBClass)
    face_recognizer = providers.Singleton(FaceRecognizer)
    app_metrica_reporter = providers.Singleton(AppMetricaReporter)
    api_connector = providers.Singleton(ApiConnector, db_class=db_class, face_recognizer=face_recognizer)
