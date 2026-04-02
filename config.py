import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    load_dotenv()
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    api_key = os.getenv("API_KEY")
    db_password = os.getenv("DB_PASSWORD")
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{db_password}@localhost/filmes_24fps"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    OMDB_API_KEY = api_key

