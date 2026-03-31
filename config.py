import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'chave_secreta'
    DB_USER = 'root'
    DB_PASSWORD = 'Keth25338921-'
    DB_HOST = 'localhost'
    DB_NAME = 'projetosoft'

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}