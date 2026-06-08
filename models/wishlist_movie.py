from datetime import datetime

from extensions import db


class WishlistMovie(db.Model):
    __tablename__ = "wishlist_movie"
    __table_args__ = (
        db.UniqueConstraint("wishlist_id", "movie_key", name="uq_wishlist_movie_key"),
    )

    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(
        db.Integer,
        db.ForeignKey("wishlist.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_key = db.Column(db.String(255), nullable=False)
    filme_id = db.Column(db.String(100), nullable=True)
    filme_titulo = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    wishlist = db.relationship("Wishlist", back_populates="movies")
