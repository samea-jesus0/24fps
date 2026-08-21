from datetime import datetime
from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    display_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    bio = db.Column(db.Text, nullable=True)
    foto = db.Column(db.String(200), default="default-avatar.svg")
    foto_pos_x = db.Column(db.Integer, default=50, nullable=False)
    foto_pos_y = db.Column(db.Integer, default=50, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    wishlists = db.relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    review_likes = db.relationship(
        "ReviewLike",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    review_comments = db.relationship(
        "ReviewComment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    received_notifications = db.relationship(
        "Notification",
        foreign_keys="Notification.recipient_user_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    created_notifications = db.relationship(
        "Notification",
        foreign_keys="Notification.actor_user_id",
        back_populates="actor",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
