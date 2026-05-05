from datetime import datetime

from extensions import db


class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    filme_id = db.Column(db.String(100), nullable=True)
    filme_titulo = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    conteudo = db.Column(db.Text, nullable=False)
    nota = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="reviews")
