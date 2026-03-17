import os

class Config:
    api_key = os.getenv("API_KEY")
    db_password = os.getenv("DB_PASSWORD")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{db_password}@localhost/filmes_24fps"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OMDB_API_KEY = api_key
    
    