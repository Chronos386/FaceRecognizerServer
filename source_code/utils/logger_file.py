import os
import logging
from datetime import datetime
from logging.handlers import BaseRotatingHandler


class CustomDateFileHandler(BaseRotatingHandler):
    def __init__(self, directory, when="midnight", backupCount=30, encoding=None):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))  # Это корневая папка проекта
        logs_dir = os.path.join(base_dir, directory)
        self.directory = logs_dir
        self.when = when
        self.backupCount = backupCount
        self.encoding = encoding
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        current_date = datetime.now().strftime("%d-%m-%Y")
        self.baseFilename = self.getFilename(current_date)
        super().__init__(self.baseFilename, 'a', encoding)

    def shouldRollover(self, record):
        current_date = datetime.now().strftime("%d-%m-%Y")
        if self.baseFilename != self.getFilename(current_date):
            return True
        return False

    def doRollover(self):
        current_date = datetime.now().strftime("%d-%m-%Y")
        self.baseFilename = self.getFilename(current_date)
        if self.stream:
            self.stream.close()
        self.stream = self._open()

    def getFilename(self, date_str):
        return os.path.join(self.directory, f"error-{date_str}.log")

    def emit(self, record):
        if self.shouldRollover(record):
            self.doRollover()
        super().emit(record)
        self.stream.write("\n\n")
        self.flush()


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = CustomDateFileHandler(directory='logs', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
