import math
from collections import defaultdict

from flask import current_app
from sqlalchemy.orm import load_only

from extensions import db
from models.review import Review
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie
from service.filme_service import (
    CATALOG_SECTIONS,
    buscar_filme_por_id,
    buscar_filme_por_nome,
    buscar_ids_filmes_por_termo,
)


MAX_WISHLIST_GENRE_LOOKUPS = 10
MAX_CANDIDATE_IDS = 18
DEFAULT_RECOMMENDATION_LIMIT = 10
DEFAULT_WEIGHTS = {"reviews": 0.60, "wishlist": 0.25, "popularity": 0.15}


def _normalize_text(value):
    return " ".join((value or "").strip().lower().split())


def _movie_key(movie_id, title):
    normalized_id = (movie_id or "").strip().lower()
    if normalized_id:
        return f"imdb:{normalized_id}"
    normalized_title = _normalize_text(title)
    return f"title:{normalized_title}" if normalized_title else None


def _parse_genres(value):
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value or "").split(",")
    return list(dict.fromkeys(
        genre.strip()
        for genre in values
        if genre and genre.strip()
    ))


def _genre_key(genre):
    return _normalize_text(genre)


def _load_user_profile(user_id):
    reviews = (
        Review.query.options(
            load_only(
                Review.id,
                Review.filme_id,
                Review.filme_titulo,
                Review.generos,
                Review.nota,
                Review.updated_at,
            )
        )
        .filter_by(user_id=user_id)
        .order_by(Review.updated_at.desc(), Review.id.desc())
        .all()
    )
    wishlist_movies = (
        WishlistMovie.query.join(Wishlist, Wishlist.id == WishlistMovie.wishlist_id)
        .options(
            load_only(
                WishlistMovie.id,
                WishlistMovie.filme_id,
                WishlistMovie.filme_titulo,
                WishlistMovie.added_at,
            )
        )
        .filter(Wishlist.user_id == user_id)
        .order_by(WishlistMovie.added_at.desc(), WishlistMovie.id.desc())
        .all()
    )

    reviewed_keys = set()
    reviewed_ids = set()
    reviewed_titles = set()
    review_by_movie = {}
    for review in reviews:
        key = _movie_key(review.filme_id, review.filme_titulo)
        if not key:
            continue
        reviewed_keys.add(key)
        if review.filme_id:
            reviewed_ids.add(review.filme_id.strip().lower())
        if title_key := _normalize_text(review.filme_titulo):
            reviewed_titles.add(title_key)
        review_by_movie.setdefault(key, review)

    rating_totals = defaultdict(float)
    rating_counts = defaultdict(int)
    for review in review_by_movie.values():
        rating = review.nota or 0
        if rating <= 0:
            continue
        preference = (rating - 3) / 2
        for genre in _parse_genres(review.generos):
            key = _genre_key(genre)
            if key:
                rating_totals[key] += preference
                rating_counts[key] += 1

    review_preferences = {
        genre: rating_totals[genre] / count
        for genre, count in rating_counts.items()
    }
    wishlisted_keys = {
        key
        for movie in wishlist_movies
        if (key := _movie_key(movie.filme_id, movie.filme_titulo))
    }
    wishlisted_ids = {
        movie.filme_id.strip().lower()
        for movie in wishlist_movies
        if movie.filme_id and movie.filme_id.strip()
    }
    wishlisted_titles = {
        title_key
        for movie in wishlist_movies
        if (title_key := _normalize_text(movie.filme_titulo))
    }
    wishlist_genres = _resolve_wishlist_genres(wishlist_movies[:MAX_WISHLIST_GENRE_LOOKUPS])

    return {
        "review_preferences": review_preferences,
        "wishlist_genres": wishlist_genres,
        "reviewed_keys": reviewed_keys,
        "wishlisted_keys": wishlisted_keys,
        "excluded_ids": reviewed_ids | wishlisted_ids,
        "excluded_titles": reviewed_titles | wishlisted_titles,
        "review_count": len(reviewed_keys),
    }


def _resolve_wishlist_genres(wishlist_movies):
    genres = set()
    for wishlist_movie in wishlist_movies:
        movie = (
            buscar_filme_por_id(wishlist_movie.filme_id)
            if wishlist_movie.filme_id
            else None
        )
        if not movie and wishlist_movie.filme_titulo:
            movie = buscar_filme_por_nome(wishlist_movie.filme_titulo)
        if movie:
            genres.update(_genre_key(genre) for genre in _parse_genres(movie.get("generos") or movie.get("genero")))
    return genres


def _load_candidates(section_genres):
    sections_by_genre = {
        _genre_key(section["genre_name"]): section
        for section in CATALOG_SECTIONS
    }
    selected_sections = []
    for genre in section_genres:
        section = sections_by_genre.get(genre)
        if section and section not in selected_sections:
            selected_sections.append(section)

    if not selected_sections:
        selected_sections = list(CATALOG_SECTIONS)

    candidate_ids = []
    seen_ids = set()
    per_section_limit = max(1, math.ceil(MAX_CANDIDATE_IDS / len(selected_sections)))
    for section in selected_sections:
        section_ids = []
        section_seen_ids = set()
        for movie_id in section.get("featured_ids", []):
            if movie_id and movie_id not in section_seen_ids:
                section_seen_ids.add(movie_id)
                section_ids.append(movie_id)

        if section_genres:
            for search_term in section.get("search_terms") or []:
                remaining_slots = per_section_limit - len(section_ids)
                if remaining_slots <= 0:
                    break
                search_ids = buscar_ids_filmes_por_termo(
                    search_term,
                    limit=min(remaining_slots, 10),
                )
                for movie_id in search_ids:
                    if movie_id and movie_id not in section_seen_ids:
                        section_seen_ids.add(movie_id)
                        section_ids.append(movie_id)
                    if len(section_ids) >= per_section_limit:
                        break

        for movie_id in section_ids:
            if movie_id and movie_id not in seen_ids:
                seen_ids.add(movie_id)
                candidate_ids.append(movie_id)
    candidate_ids = candidate_ids[:MAX_CANDIDATE_IDS]

    movies = []
    for rank, movie_id in enumerate(candidate_ids):
        movie = buscar_filme_por_id(movie_id)
        if movie:
            movie["rank"] = rank
            movies.append(movie)
    return movies


def _get_weights():
    configured = current_app.config.get("RECOMMENDATION_WEIGHTS", DEFAULT_WEIGHTS)
    weights = {}
    for key, default in DEFAULT_WEIGHTS.items():
        try:
            value = float(configured.get(key, default))
        except (AttributeError, TypeError, ValueError):
            value = default
        weights[key] = value if math.isfinite(value) and value >= 0 else default
    return weights


def _score_candidate(movie, review_preferences, wishlist_genres, weights):
    genres = _parse_genres(movie.get("generos") or movie.get("genero"))
    genre_keys = [_genre_key(genre) for genre in genres]
    signals = {}

    if review_preferences and genre_keys:
        signed_affinity = sum(
            review_preferences.get(genre, 0)
            for genre in genre_keys
        )
        signed_affinity /= len(genre_keys)
        signals["reviews"] = (signed_affinity + 1) / 2

    if wishlist_genres and genre_keys:
        signals["wishlist"] = len(set(genre_keys) & wishlist_genres) / len(genre_keys)

    try:
        imdb_rating = float(movie.get("imdb_valor"))
    except (TypeError, ValueError):
        imdb_rating = 0
    signals["popularity"] = max(0, min(imdb_rating, 10)) / 10

    active_weight_total = sum(weights[key] for key in signals)
    score = (
        sum(signals[key] * weights[key] for key in signals) / active_weight_total
        if active_weight_total
        else 0
    )
    positive_review_matches = [
        genre for genre in genres
        if review_preferences.get(_genre_key(genre), 0) > 0
    ]
    if positive_review_matches:
        favorite = max(
            positive_review_matches,
            key=lambda genre: review_preferences[_genre_key(genre)],
        )
        reason = f"Porque você gosta de {favorite}"
    else:
        wishlist_match = next(
            (genre for genre in genres if _genre_key(genre) in wishlist_genres),
            None,
        )
        if wishlist_match:
            reason = f"Porque {wishlist_match} está na sua wishlist"
        elif imdb_rating:
            reason = "Bem avaliado no IMDb"
        else:
            reason = "Uma sugestão para explorar"

    return score, reason


def get_movie_recommendations(
    user_id,
    limit=DEFAULT_RECOMMENDATION_LIMIT,
    rotation=0,
):
    try:
        limit = max(1, min(int(limit), 20))
    except (TypeError, ValueError):
        limit = DEFAULT_RECOMMENDATION_LIMIT
    try:
        rotation = max(0, int(rotation))
    except (TypeError, ValueError):
        rotation = 0

    profile = _load_user_profile(user_id)
    positive_genres = sorted(
        (
            genre for genre, preference in profile["review_preferences"].items()
            if preference > 0
        ),
        key=lambda genre: (-profile["review_preferences"][genre], genre),
    )
    wishlist_genres = sorted(profile["wishlist_genres"])
    section_genres = list(dict.fromkeys(positive_genres + wishlist_genres))[:3]

    movies = _load_candidates(section_genres)
    weights = _get_weights()
    recommendations = []
    seen_keys = set(profile["reviewed_keys"] | profile["wishlisted_keys"])
    seen_titles = set(profile["excluded_titles"])

    for movie in movies:
        movie_id = movie.get("id")
        title = (movie.get("titulo") or "").strip()
        key = _movie_key(movie_id, title)
        title_key = _normalize_text(title)
        if (
            not key
            or key in seen_keys
            or (movie_id and movie_id.strip().lower() in profile["excluded_ids"])
            or (title_key and title_key in seen_titles)
        ):
            continue
        seen_keys.add(key)
        if title_key:
            seen_titles.add(title_key)

        genres = _parse_genres(movie.get("generos") or movie.get("genero"))
        score, reason = _score_candidate(
            movie,
            profile["review_preferences"],
            profile["wishlist_genres"],
            weights,
        )
        recommendations.append(
            {
                "id": movie_id,
                "title": title,
                "poster": movie.get("poster"),
                "genres": genres,
                "synopsis": (movie.get("sinopse") or "")[:280],
                "rating": movie.get("imdb"),
                "score": round(score * 100, 1),
                "reason": reason,
            }
        )

    recommendations.sort(
        key=lambda movie: (-movie["score"], movie["title"].lower()),
    )
    candidate_pool = recommendations[:max(limit, limit * 2)]
    if len(candidate_pool) <= limit:
        return candidate_pool

    start = (rotation * limit) % len(candidate_pool)
    rotated_pool = candidate_pool[start:] + candidate_pool[:start]
    return rotated_pool[:limit]
