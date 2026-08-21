from datetime import datetime

from extensions import db


class ReviewComment(db.Model):
    __tablename__ = "review_comment"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("review.id", ondelete="CASCADE"), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="review_comments")
    review = db.relationship("Review", back_populates="comments")
