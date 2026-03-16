import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Guapitos123$@localhost/filmes_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OMDB_API_KEY = "SUA_CHAVE_AQUI"