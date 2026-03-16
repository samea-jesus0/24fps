import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Guapitos123$@localhost/filmes_24fps"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OMDB_API_KEY = "3b854b62"