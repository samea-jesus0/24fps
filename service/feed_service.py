from flask import url_for
from sqlalchemy.orm import joinedload

from extensions import db
from models.review import Review
from models.user import User
from models.user_follow import UserFollow
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie


FEED_LIMIT = 50


def _isoformat(value):
    return value.isoformat() if value else None


def _avatar_url(user):
    filename = user.foto if user.foto and user.foto != "default.png" else "default-avatar.svg"
    return url_for("static", filename=f"uploads/{filename}")


def _user_payload(user):
    return {
        "id": user.id,
        "displayName": user.display_name or user.nome or "Usuario",
        "avatarUrl": _avatar_url(user),
        "profileUrl": url_for("users.public_profile", user_id=user.id),
    }


def _review_activities(reviews):
    activities = []
    for review in reviews:
        actor = _user_payload(review.user)
        movie_title = review.filme_titulo or "um filme"
        movie_url = url_for("movie.index", filme=movie_title)
        timestamp = review.created_at or review.updated_at

        if review.nota and review.nota > 0:
            activities.append(
                {
                    "type": "rating",
                    "actor": actor,
                    "movieId": review.filme_id,
                    "movieTitle": movie_title,
                    "movieUrl": movie_url,
                    "posterUrl": review.poster_url,
                    "rating": review.nota,
                    "timestamp": _isoformat(timestamp),
                    "text": f"{actor['displayName']} avaliou {movie_title} com {review.nota} estrelas.",
                }
            )

        if (review.conteudo or "").strip():
            activities.append(
                {
                    "type": "review",
                    "actor": actor,
                    "movieId": review.filme_id,
                    "movieTitle": movie_title,
                    "movieUrl": movie_url,
                    "posterUrl": review.poster_url,
                    "rating": review.nota or 0,
                    "timestamp": _isoformat(timestamp),
                    "text": f"{actor['displayName']} publicou uma resenha de {movie_title}.",
                    "reviewUrl": url_for("interactions.review_detail", review_id=review.id),
                }
            )

    return activities


def _wishlist_activities(movies):
    activities = []
    for movie in movies:
        wishlist = movie.wishlist
        actor = _user_payload(wishlist.user)
        movie_title = movie.filme_titulo or "um filme"
        timestamp = movie.added_at or wishlist.updated_at or wishlist.created_at

        activities.append(
            {
                "type": "wishlist_movie",
                "actor": actor,
                "movieId": movie.filme_id,
                "movieTitle": movie_title,
                "movieUrl": url_for("movie.index", filme=movie_title),
                "posterUrl": movie.poster_url,
                "wishlistId": wishlist.id,
                "wishlistTitle": wishlist.titulo,
                "timestamp": _isoformat(timestamp),
                "text": (
                    f"{actor['displayName']} adicionou {movie_title} "
                    f'à lista "{wishlist.titulo}".'
                ),
            }
        )

    return activities


def get_following_feed(user_id, limit=FEED_LIMIT):
    following_ids = [
        row.followed_user_id
        for row in UserFollow.query.with_entities(UserFollow.followed_user_id)
        .filter(UserFollow.follower_user_id == user_id)
        .all()
    ]

    if not following_ids:
        return []

    review_limit = max(limit, 10)
    reviews = (
        Review.query.options(joinedload(Review.user))
        .filter(Review.user_id.in_(following_ids))
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(review_limit)
        .all()
    )

    wishlist_movies = (
        WishlistMovie.query
        .join(Wishlist, Wishlist.id == WishlistMovie.wishlist_id)
        .options(joinedload(WishlistMovie.wishlist).joinedload(Wishlist.user))
        .filter(
            Wishlist.user_id.in_(following_ids),
            Wishlist.is_public.is_(True),
        )
        .order_by(WishlistMovie.added_at.desc(), WishlistMovie.id.desc())
        .limit(review_limit)
        .all()
    )

    activities = _review_activities(reviews)
    activities.extend(_wishlist_activities(wishlist_movies))
    activities.sort(
        key=lambda activity: (activity.get("timestamp") or "", activity.get("type") or ""),
        reverse=True,
    )
    return activities[:limit]
