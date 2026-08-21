from datetime import datetime

from extensions import db


class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("review.id", ondelete="CASCADE"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey("review_comment.id", ondelete="CASCADE"), nullable=True)
    type = db.Column(db.String(20), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_user_id],
        back_populates="received_notifications",
    )
    actor = db.relationship(
        "User",
        foreign_keys=[actor_user_id],
        back_populates="created_notifications",
    )
    review = db.relationship("Review", back_populates="notifications")
    comment = db.relationship("ReviewComment")
