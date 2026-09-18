from datetime import datetime

from extensions import db


class UserFollow(db.Model):
    __tablename__ = "user_follow"
    __table_args__ = (
        db.UniqueConstraint("follower_user_id", "followed_user_id", name="uq_user_follow"),
    )

    id = db.Column(db.Integer, primary_key=True)
    follower_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    followed_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    follower_user = db.relationship(
        "User",
        foreign_keys=[follower_user_id],
        back_populates="following",
    )
    followed_user = db.relationship(
        "User",
        foreign_keys=[followed_user_id],
        back_populates="followers",
    )
