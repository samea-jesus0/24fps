from datetime import datetime

from flask import url_for
from sqlalchemy import func, or_

from extensions import db
from models.review import Review
from models.user import User


DEFAULT_AVATAR = "default-avatar.svg"
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


def _isoformat(value):
    return value.isoformat() if value else None


def _date_label(value):
    if not value:
        return "Data nao informada"
    return value.strftime("%d/%m/%Y")


def _review_payload(review):
    return {
        "id": review.id,
        "movieId": review.filme_id,
        "movieTitle": review.filme_titulo,
        "posterUrl": review.poster_url,
        "content": review.conteudo,
        "rating": review.nota or 0,
        "createdAt": _isoformat(review.created_at),
        "createdAtLabel": _date_label(review.created_at),
        "updatedAt": _isoformat(review.updated_at),
        "movieUrl": _movie_url(review),
    }


def _activity_payload(kind, label, description, created_at, target_url=None):
    return {
        "type": kind,
        "label": label,
        "description": description,
        "createdAt": _isoformat(created_at),
        "createdAtLabel": _date_label(created_at),
        "targetUrl": target_url,
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
    # O projeto atual ainda nao possui modelo de listas/watchlist no codigo.
    # Mantemos a chave no DTO para preservar o contrato do F07.
    return []


def get_public_user_profile(user_id, external_urls=False):
    user = db.session.get(User, user_id)
    if not user:
        return None

    recent_reviews = (
        Review.query.filter_by(user_id=user.id)
        .order_by(Review.created_at.desc(), Review.updated_at.desc())
        .limit(RECENT_REVIEWS_LIMIT)
        .all()
    )
    review_count = Review.query.filter_by(user_id=user.id).count()
    public_lists = _load_public_lists(user.id)

    return {
        "id": user.id,
        "username": user.nome or f"usuario-{user.id}",
        "displayName": user.display_name or user.nome or f"Usuario {user.id}",
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
        "recentReviews": [_review_payload(review) for review in recent_reviews],
        "lists": public_lists,
        "recentActivities": _build_recent_activities(recent_reviews),
    }


def search_public_users(query, limit=8):
    query = (query or "").strip()
    if len(query) < 2:
        return []

    users = (
        User.query.filter(
            or_(
                User.nome.ilike(f"%{query}%"),
                User.display_name.ilike(f"%{query}%"),
            )
        )
        .order_by(User.nome.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.nome or f"usuario-{user.id}",
            "displayName": user.display_name or user.nome or f"Usuario {user.id}",
            "bio": user.bio or "",
            "avatarUrl": _avatar_url(user),
            "profileUrl": url_for("users.public_profile", user_id=user.id),
        }
        for user in users
    ]
