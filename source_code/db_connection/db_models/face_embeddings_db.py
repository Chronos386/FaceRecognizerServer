from sqlalchemy import *
from source_code.db_connection.db_models.base import Base


class FaceEmbeddingsDB(Base):
    __tablename__ = 'face_embeddings'
    id = Column(Integer, primary_key=True)
    embedding = Column(ARRAY(Float), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    path_photo = Column(String(300), nullable=False)

    def __repr__(self):
        return f'{self.id} {self.embedding} {self.student_id}'
