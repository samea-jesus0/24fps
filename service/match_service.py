"""Compatibility scores built only from public review history already in the database."""

from collections import Counter, defaultdict
from math import sqrt

from flask import url_for
from sqlalchemy.orm import load_only

from extensions import db
from models.review import Review
from models.user import User
from models.user_follow import UserFollow
from service.user_statistics_service import _movie_key_from_values


# These weights express the intended importance when each signal is available.
COMPONENT_WEIGHTS = {"ratings": 0.60, "genres": 0.30, "movies": 0.10}
# One to four shared reviewed movies is a low-confidence sample; 5-14 is medium;
# 15 or more is high. Rating similarity itself reaches full weight at five shared
# positive ratings so one lucky match cannot produce a 100% overall score.
LOW_CONFIDENCE_MAX = 4
MEDIUM_CONFIDENCE_MAX = 14
RATING_RELIABILITY_SAMPLE_SIZE = 5
COMMON_GENRES_LIMIT = 5
MATCHES_LIMIT = 50


def _normalise_genre(value):
    return " ".join((value or "").strip().casefold().split())


def _display_genre(value):
    return " ".join((value or "").strip().split())


def _parse_genres(value):
    if not value:
        return []

    parsed = []
    seen = set()
    for raw_genre in str(value).split(","):
        canonical = _normalise_genre(raw_genre)
        if canonical and canonical not in seen:
            seen.add(canonical)
            parsed.append((canonical, _display_genre(raw_genre)))
    return parsed


def _safe_rating(value):
    try:
        rating = int(value)
    except (TypeError, ValueError):
        return None
    return rating if 1 <= rating <= 5 else None


def _confidence(common_movies_count):
    if common_movies_count <= LOW_CONFIDENCE_MAX:
        return "low"
    if common_movies_count <= MEDIUM_CONFIDENCE_MAX:
        return "medium"
    return "high"


def _percent(value):
    if value is None:
        return None
    return max(0, min(100, int(value + 0.5)))


def _avatar_url(user):
    filename = user.foto if user.foto and user.foto != "default.png" else "default-avatar.svg"
    return url_for("static", filename=f"uploads/{filename}")


def _unique_movies(reviews):
    """Deduplicate as profile statistics do: IMDb ID first, normalised title fallback.

    The newest review supplies the rating. If its genre metadata is empty, keep
    the newest older metadata found for that same movie.
    """
    movies = {}
    for review in reviews:
        movie_key = _movie_key_from_values(review.filme_id, review.filme_titulo)
        if not movie_key or movie_key == "title:":
            continue

        candidate_genres = _parse_genres(review.generos)
        existing = movies.get(movie_key)
        if existing is None:
            movies[movie_key] = {
                "key": movie_key,
                "movie_id": review.filme_id,
                "title": review.filme_titulo or "Filme sem título",
                "rating": _safe_rating(review.nota),
                "genres": candidate_genres,
            }
        elif not existing["genres"] and candidate_genres:
            existing["genres"] = candidate_genres
    return movies


def _user_movie_data(reviews):
    movies = _unique_movies(reviews)
    genre_counts = Counter()
    genre_labels = {}

    for movie in movies.values():
        for genre_key, label in movie["genres"]:
            genre_counts[genre_key] += 1
            genre_labels.setdefault(genre_key, label)

    return {"movies": movies, "genre_counts": genre_counts, "genre_labels": genre_labels}


def _rating_similarity(current_movies, other_movies):
    common_keys = current_movies.keys() & other_movies.keys()
    comparisons = []
    for movie_key in common_keys:
        current_rating = current_movies[movie_key]["rating"]
        other_rating = other_movies[movie_key]["rating"]
        if current_rating is None or other_rating is None:
            continue
        # On the 0-5 scale each point of difference removes 20 percentage points.
        comparisons.append(100 - 20 * abs(current_rating - other_rating))

    if not comparisons:
        return None, 0
    return sum(comparisons) / len(comparisons), len(comparisons)


def _genre_similarity(current_data, other_data):
    current_counts = current_data["genre_counts"]
    other_counts = other_data["genre_counts"]
    if not current_counts or not other_counts:
        return None

    dot_product = sum(count * other_counts.get(genre, 0) for genre, count in current_counts.items())
    current_norm = sqrt(sum(count * count for count in current_counts.values()))
    other_norm = sqrt(sum(count * count for count in other_counts.values()))
    if not current_norm or not other_norm:
        return None
    return 100 * dot_product / (current_norm * other_norm)


def _common_genres(current_data, other_data):
    current_counts = current_data["genre_counts"]
    other_counts = other_data["genre_counts"]
    shared = current_counts.keys() & other_counts.keys()
    ordered = sorted(
        shared,
        key=lambda genre: (
            -min(current_counts[genre], other_counts[genre]),
            -(current_counts[genre] + other_counts[genre]),
            genre,
        ),
    )
    return [
        current_data["genre_labels"].get(genre)
        or other_data["genre_labels"].get(genre)
        or genre
        for genre in ordered[:COMMON_GENRES_LIMIT]
    ]


def _movie_similarity(current_movies, other_movies):
    union_count = len(current_movies.keys() | other_movies.keys())
    if not union_count:
        return None
    return 100 * len(current_movies.keys() & other_movies.keys()) / union_count


def _compatibility(current_data, other_data):
    current_movies = current_data["movies"]
    other_movies = other_data["movies"]
    common_keys = current_movies.keys() & other_movies.keys()
    common_movies_count = len(common_keys)

    raw_ratings, ratings_sample_count = _rating_similarity(current_movies, other_movies)
    if raw_ratings is None:
        reliable_ratings = None
    else:
        # Pull small rating samples toward neutral (50%) to avoid overconfident matches.
        reliability = min(1.0, ratings_sample_count / RATING_RELIABILITY_SAMPLE_SIZE)
        reliable_ratings = 50 + (raw_ratings - 50) * reliability

    genres = _genre_similarity(current_data, other_data)
    movies = _movie_similarity(current_movies, other_movies)
    component_values = {"ratings": reliable_ratings, "genres": genres, "movies": movies}
    active_weight = sum(COMPONENT_WEIGHTS[name] for name, value in component_values.items() if value is not None)
    score = (
        sum(COMPONENT_WEIGHTS[name] * value for name, value in component_values.items() if value is not None)
        / active_weight
        if active_weight
        else 0
    )

    common_movie_details = []
    for movie_key in common_keys:
        current_movie = current_movies[movie_key]
        other_movie = other_movies[movie_key]
        common_movie_details.append(
            {
                "movieId": current_movie["movie_id"] or other_movie["movie_id"],
                "title": current_movie["title"] or other_movie["title"],
                # Zero means no rating in this app; expose it as null in comparisons.
                "currentUserRating": current_movie["rating"],
                "otherUserRating": other_movie["rating"],
            }
        )
    common_movie_details.sort(key=lambda movie: (movie["title"] or "").casefold())

    has_history = bool(current_movies and other_movies)
    result = {
        "compatibility": _percent(score),
        "confidence": _confidence(common_movies_count),
        "commonMoviesCount": common_movies_count,
        "commonRatedMoviesCount": ratings_sample_count,
        "commonGenres": _common_genres(current_data, other_data),
        "components": {
            "ratings": _percent(reliable_ratings),
            "ratingsRaw": _percent(raw_ratings),
            "genres": _percent(genres),
            "movies": _percent(movies),
        },
        "commonMovies": common_movie_details,
        "hasComparisonData": has_history,
        "currentUserHasHistory": bool(current_movies),
        "otherUserHasHistory": bool(other_movies),
    }
    if not has_history:
        result["message"] = "Ainda não há histórico de resenhas suficiente para comparar os perfis."
    elif result["compatibility"] >= 85:
        result["message"] = "Vocês têm gostos cinematográficos muito parecidos."
    elif result["compatibility"] >= 70:
        result["message"] = "Vocês compartilham várias preferências cinematográficas."
    elif result["compatibility"] >= 50:
        result["message"] = "Vocês têm algumas preferências cinematográficas em comum."
    else:
        result["message"] = "Os gostos cinematográficos de vocês seguem caminhos diferentes."
    return result


def _load_review_data(user_ids):
    grouped_reviews = defaultdict(list)
    if not user_ids:
        return grouped_reviews

    reviews = (
        Review.query.options(
            load_only(
                Review.id,
                Review.user_id,
                Review.filme_id,
                Review.filme_titulo,
                Review.generos,
                Review.nota,
                Review.created_at,
                Review.updated_at,
            )
        )
        .filter(Review.user_id.in_(user_ids))
        .order_by(Review.user_id.asc(), Review.created_at.desc(), Review.updated_at.desc(), Review.id.desc())
        .all()
    )
    for review in reviews:
        grouped_reviews[review.user_id].append(review)
    return {user_id: _user_movie_data(user_reviews) for user_id, user_reviews in grouped_reviews.items()}


def _public_user_data(user):
    return {
        "userId": user.id,
        "name": (user.display_name or user.nome or f"Usuário {user.id}").strip(),
        "username": (user.nome or f"usuario-{user.id}").strip(),
        "avatarUrl": _avatar_url(user),
        "profileUrl": url_for("users.public_profile", user_id=user.id),
    }


def _build_user_matches(user_id, limit=MATCHES_LIMIT):
    """Return matches and the current user's history flag with batched queries."""
    users = User.query.filter(User.id != user_id).order_by(User.id.asc()).all()
    candidate_ids = [user.id for user in users]
    review_data = _load_review_data([user_id, *candidate_ids])
    current_data = review_data.get(user_id, _user_movie_data([]))
    if not current_data["movies"]:
        return [], False

    users_with_history = [user for user in users if review_data.get(user.id, {}).get("movies")]
    if not users_with_history:
        return [], True

    following_ids = {
        followed_id
        for (followed_id,) in db.session.query(UserFollow.followed_user_id)
        .filter(
            UserFollow.follower_user_id == user_id,
            UserFollow.followed_user_id.in_([user.id for user in users_with_history]),
        )
        .all()
    }

    matches = []
    for user in users_with_history:
        result = _compatibility(current_data, review_data[user.id])
        matches.append(
            {
                **_public_user_data(user),
                **{key: result[key] for key in (
                    "compatibility",
                    "confidence",
                    "commonMoviesCount",
                    "commonRatedMoviesCount",
                    "commonGenres",
                    "components",
                    "message",
                    "hasComparisonData",
                )},
                "isFollowing": user.id in following_ids,
            }
        )

    matches.sort(
        key=lambda match: (
            -match["compatibility"],
            match["isFollowing"],
            match["name"].casefold(),
            match["userId"],
        )
    )
    return matches[: max(0, int(limit))], True


def get_user_matches(user_id, limit=MATCHES_LIMIT):
    """Return the best data-backed matches using batched user/review/follow queries."""
    matches, _ = _build_user_matches(user_id, limit=limit)
    return matches


def get_match_page_data(user_id, limit=MATCHES_LIMIT):
    """Return page results and whether the signed-in user has usable movie history."""
    matches, has_history = _build_user_matches(user_id, limit=limit)
    return {"matches": matches, "hasHistory": has_history}


def get_match_details(current_user_id, other_user_id):
    """Return one public-history comparison, or None when the other user is missing."""
    other_user = db.session.get(User, other_user_id)
    if not other_user:
        return None

    current_data_by_id = _load_review_data([current_user_id, other_user_id])
    current_data = current_data_by_id.get(current_user_id, _user_movie_data([]))
    other_data = current_data_by_id.get(other_user_id, _user_movie_data([]))
    result = _compatibility(current_data, other_data)
    following = (
        current_user_id != other_user_id
        and UserFollow.query.filter_by(
            follower_user_id=current_user_id,
            followed_user_id=other_user_id,
        ).first()
        is not None
    )
    return {**_public_user_data(other_user), **result, "isFollowing": following}
