from datetime import datetime

from flask import url_for
from sqlalchemy import func, or_

from extensions import db
from models.review import Review
from models.review_comment import ReviewComment
from models.review_like import ReviewLike
from models.user import User
from service.wishlist_service import list_public_wishlists


DEFAULT_AVATAR = "default-avatar.svg"
USER_DIRECTORY_LIMIT = 12
RECENT_REVIEWS_LIMIT = 6
RECENT_ACTIVITIES_LIMIT = 8


def _avatar_filename(user):
    if user.foto and user.foto != "default.png":
        return user.foto
    return DEFAULT_AVATAR


def _avatar_url(user, external=False):
    return url_for(
        "static",
        filename=f"uploads/{_avatar_filename(user)}",
        _external=external,
    )


def _movie_url(review):
    if not review.filme_titulo:
        return url_for("movie.index")
    return url_for("movie.index", filme=review.filme_titulo)


def _username(user):
    return (user.nome or f"usuario-{user.id}").strip()


def _display_name(user):
    return (user.display_name or user.nome or f"Usuario {user.id}").strip()


def _isoformat(value):
    return value.isoformat() if value else None


def _date_label(value):
    if not value:
        return "Data nao informada"
    return value.strftime("%d/%m/%Y")


def _review_payload(review, viewer_user_id=None, highlighted_review_id=None):
    like_count = ReviewLike.query.filter_by(review_id=review.id).count()
    comment_count = ReviewComment.query.filter_by(review_id=review.id).count()
    liked_by_current_user = False
    if viewer_user_id:
        liked_by_current_user = (
            ReviewLike.query.filter_by(review_id=review.id, user_id=viewer_user_id).first() is not None
        )

    return {
        "id": review.id,
        "authorId": review.user_id,
        "movieId": review.filme_id,
        "movieTitle": review.filme_titulo,
        "posterUrl": review.poster_url,
        "content": review.conteudo,
        "rating": review.nota or 0,
        "createdAt": _isoformat(review.created_at),
        "createdAtLabel": _date_label(review.created_at),
        "updatedAt": _isoformat(review.updated_at),
        "movieUrl": _movie_url(review),
        "reviewUrl": url_for("interactions.review_detail", review_id=review.id),
        "likeCount": like_count,
        "commentCount": comment_count,
        "likedByCurrentUser": liked_by_current_user,
        "canInteract": bool(viewer_user_id and viewer_user_id != review.user_id),
        "isHighlighted": review.id == highlighted_review_id,
    }


def _activity_payload(
    kind,
    label,
    description,
    created_at,
    target_url=None,
    movie_id=None,
    movie_title=None,
    poster_url=None,
    review_content=None,
    rating=None,
):
    return {
        "type": kind,
        "label": label,
        "description": description,
        "createdAt": _isoformat(created_at),
        "createdAtLabel": _date_label(created_at),
        "targetUrl": target_url,
        "movieId": movie_id,
        "movieTitle": movie_title,
        "posterUrl": poster_url,
        "reviewContent": review_content,
        "rating": rating,
    }


def _build_recent_activities(reviews):
    activities = []

    for review in reviews:
        movie_title = review.filme_titulo or "um filme"
        target_url = _movie_url(review)

        activities.append(
            _activity_payload(
                "review_created",
                "Resenha criada",
                f"Publicou uma resenha de {movie_title}.",
                review.created_at or review.updated_at,
                target_url,
                movie_id=review.filme_id,
                movie_title=review.filme_titulo,
                poster_url=review.poster_url,
                review_content=review.conteudo,
                rating=review.nota or 0,
            )
        )

        if review.nota and review.nota > 0:
            activities.append(
                _activity_payload(
                    "movie_rated",
                    "Filme avaliado",
                    f"Avaliou {movie_title} com {review.nota}/5.",
                    review.created_at or review.updated_at,
                    target_url,
                    movie_id=review.filme_id,
                    movie_title=review.filme_titulo,
                    poster_url=review.poster_url,
                    review_content=review.conteudo,
                    rating=review.nota or 0,
                )
            )

    activities.sort(
        key=lambda item: datetime.fromisoformat(item["createdAt"]) if item.get("createdAt") else datetime.min,
        reverse=True,
    )
    return activities[:RECENT_ACTIVITIES_LIMIT]


def _count_reviewed_movies(user_id):
    reviewed_movies = (
        db.session.query(func.count(func.distinct(func.coalesce(Review.filme_id, Review.filme_titulo))))
        .filter(Review.user_id == user_id, Review.nota > 0)
        .scalar()
    )
    return reviewed_movies or 0


def _load_public_lists(user_id):
    return list_public_wishlists(user_id)


def _public_user_card_payload(user, external_urls=False):
    return {
        "id": user.id,
        "username": _username(user),
        "displayName": _display_name(user),
        "bio": user.bio or "",
        "avatarUrl": _avatar_url(user, external=external_urls),
        "avatarPosition": {
            "x": user.foto_pos_x or 50,
            "y": user.foto_pos_y or 50,
        },
        "createdAt": _isoformat(user.created_at),
        "createdAtLabel": _date_label(user.created_at),
        "profileUrl": url_for("users.public_profile", user_id=user.id),
    }


def _public_users_query(exclude_user_id=None):
    query = User.query
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query


def list_public_users(limit=USER_DIRECTORY_LIMIT, exclude_user_id=None, external_urls=False):
    users = (
        _public_users_query(exclude_user_id=exclude_user_id)
        .order_by(User.created_at.desc(), User.nome.asc())
        .limit(limit)
        .all()
    )

    return [_public_user_card_payload(user, external_urls=external_urls) for user in users]


def get_public_user_profile(
    user_id,
    external_urls=False,
    viewer_user_id=None,
    highlighted_review_id=None,
):
    user = db.session.get(User, user_id)
    if not user:
        return None

    recent_reviews = (
        Review.query.filter_by(user_id=user.id)
        .order_by(Review.created_at.desc(), Review.updated_at.desc())
        .limit(RECENT_REVIEWS_LIMIT)
        .all()
    )
    if highlighted_review_id and not any(review.id == highlighted_review_id for review in recent_reviews):
        highlighted_review = Review.query.filter_by(id=highlighted_review_id, user_id=user.id).first()
        if highlighted_review:
            recent_reviews = [highlighted_review, *recent_reviews[: RECENT_REVIEWS_LIMIT - 1]]
    review_count = Review.query.filter_by(user_id=user.id).count()
    public_lists = _load_public_lists(user.id)

    return {
        "id": user.id,
        "username": _username(user),
        "displayName": _display_name(user),
        "bio": user.bio or "",
        "avatarUrl": _avatar_url(user, external=external_urls),
        "avatarPosition": {
            "x": user.foto_pos_x or 50,
            "y": user.foto_pos_y or 50,
        },
        "createdAt": _isoformat(user.created_at),
        "createdAtLabel": _date_label(user.created_at),
        "stats": {
            "reviews": review_count,
            "ratings": _count_reviewed_movies(user.id),
            "lists": len(public_lists),
            "watchlist": 0,
        },
        "recentReviews": [
            _review_payload(
                review,
                viewer_user_id=viewer_user_id,
                highlighted_review_id=highlighted_review_id,
            )
            for review in recent_reviews
        ],
        "lists": public_lists,
        "recentActivities": _build_recent_activities(recent_reviews),
    }


def search_public_users(query, limit=USER_DIRECTORY_LIMIT, exclude_user_id=None, external_urls=False):
    query = (query or "").strip()
    if len(query) < 2:
        return []

    users = (
        _public_users_query(exclude_user_id=exclude_user_id)
        .filter(
            or_(
                User.nome.ilike(f"%{query}%"),
                User.display_name.ilike(f"%{query}%"),
            )
        )
        .order_by(func.coalesce(User.display_name, User.nome).asc(), User.nome.asc())
        .limit(limit)
        .all()
    )

    return [_public_user_card_payload(user, external_urls=external_urls) for user in users]
