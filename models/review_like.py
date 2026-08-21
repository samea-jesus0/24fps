from datetime import datetime

from extensions import db


class ReviewLike(db.Model):
    __tablename__ = "review_like"
    __table_args__ = (
        db.UniqueConstraint("user_id", "review_id", name="uq_review_like_user_review"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("review.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="review_likes")
    review = db.relationship("Review", back_populates="likes")
