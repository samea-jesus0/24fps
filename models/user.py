from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    foto = db.Column(db.String(200), default="default-avatar.svg")
    foto_pos_x = db.Column(db.Integer, default=50, nullable=False)
    foto_pos_y = db.Column(db.Integer, default=50, nullable=False)
