import cv2
import time
import faiss
import threading
import numpy as np
from typing import Optional, Tuple, List
from insightface.app import FaceAnalysis
from werkzeug.datastructures import FileStorage
from source_code.utils.logger_file import logger


class FaceRecognizer:
    def __init__(self):
        self.local = threading.local()

    def __getApp(self):
        if not hasattr(self.local, "app"):
            self.local.app = FaceAnalysis(allowed_modules=['detection', 'recognition'], providers=['CPUExecutionProvider'])
            self.local.app.prepare(ctx_id=-1)
        return self.local.app

    def __getFaceEmbedding(self, img: cv2.typing.MatLike) -> Tuple[Optional[np.ndarray], int]:
        if img is None:
            logger.error(f"Не удалось загрузить изображение", exc_info=True)
            return None, 1
        img_1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        app = self.__getApp()
        faces = app.get(img_1)
        if len(faces) == 0:
            logger.error(f"Лицо не обнаружено на изображении", exc_info=True)
            return None, 2
        if len(faces) != 1:
            logger.error(f"На изображении обнаружено несколько лиц", exc_info=True)
            return None, 3
        face = faces[0]
        embedding = face.embedding
        return embedding, 0

    def recognizeFace(self, file_storage: FileStorage, embeddings: np.vstack) -> Tuple[Optional[List[int]], int]:
        try:
            start_time = time.time()

            file_bytes = file_storage.read()
            np_arr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            emb, code = self.__getFaceEmbedding(img)
            if code != 0:
                return None, code
            index = faiss.IndexFlatL2(512)
            index.add(embeddings)
            emb = np.array([emb], dtype='float32')
            distances, indices = index.search(emb, 3)
            emb_list = []
            for i in range(0, len(distances.tolist()[0])):
                if distances.tolist()[0][i] < 500:
                    emb_list.append(indices.tolist()[0][i])
            if len(emb_list) == 0:
                return None, 4

            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Время выполнения распознавания: {execution_time} секунд")

            return emb_list, 0
        except Exception as e:
            logger.error(f"Ошибка в recognizeFace: {e}", exc_info=True)
            return None, -1

    def getEmbedding(self, img) -> Tuple[Optional[np.ndarray], int]:
        try:
            emb, code = self.__getFaceEmbedding(img)
            if code != 0:
                return None, code
            return emb, 0
        except Exception as e:
            logger.error(f"Ошибка в getEmbedding: {e}", exc_info=True)
            return None, -1
