from collections import Counter

from sqlalchemy import extract, func
from sqlalchemy.orm import load_only

from extensions import db
from models.review import Review
from models.user import User
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie
from service.filme_service import resolver_metadados_filme


TOP_GENRES_LIMIT = 5
RATING_SCALE = 5


def _normalize_text(value):
    return " ".join((value or "").strip().lower().split())


def _movie_key_from_values(movie_id, title):
    movie_id = (movie_id or "").strip().lower()
    if movie_id:
        return f"imdb:{movie_id}"
    return f"title:{_normalize_text(title)}"


def _movie_key(review):
    return _movie_key_from_values(review.filme_id, review.filme_titulo)


def _movie_key_expression():
    movie_id = func.lower(func.trim(Review.filme_id))
    title = func.lower(func.trim(Review.filme_titulo))
    return func.coalesce(func.nullif(movie_id, ""), title)


def _parse_genres(value):
    if not value:
        return []

    return [genre.strip() for genre in str(value).split(",") if genre.strip()]


def _scalar_count(query):
    return int(query.scalar() or 0)


def _count_distinct_watched_movies(user_id):
    return _scalar_count(
        db.session.query(func.count(func.distinct(_movie_key_expression()))).filter(Review.user_id == user_id)
    )


def _average_rating(user_id):
    average = (
        db.session.query(func.avg(Review.nota))
        .filter(Review.user_id == user_id, Review.nota > 0)
        .scalar()
    )
    return round(float(average), 1) if average is not None else None


def _rating_count(user_id):
    return _scalar_count(db.session.query(func.count(Review.id)).filter(Review.user_id == user_id, Review.nota > 0))


def _watched_by_year(user_id):
    movie_key = _movie_key_expression()
    first_watches = (
        db.session.query(
            movie_key.label("movie_key"),
            func.min(Review.created_at).label("watched_at"),
        )
        .filter(Review.user_id == user_id, Review.created_at.isnot(None))
        .group_by(movie_key)
        .subquery()
    )
    watched_year = extract("year", first_watches.c.watched_at)

    rows = (
        db.session.query(
            watched_year.label("year"),
            func.count(first_watches.c.movie_key).label("movie_count"),
        )
        .filter(first_watches.c.watched_at.isnot(None))
        .group_by(watched_year)
        .order_by(watched_year.asc())
        .all()
    )

    return [
        {"year": int(row.year), "count": int(row.movie_count)}
        for row in rows
        if row.year is not None
    ]


def _public_list_counts(user_id):
    total_lists = _scalar_count(
        db.session.query(func.count(Wishlist.id)).filter(
            Wishlist.user_id == user_id,
            Wishlist.is_public.is_(True),
        )
    )
    total_movies = _scalar_count(
        db.session.query(func.count(WishlistMovie.id))
        .join(Wishlist, WishlistMovie.wishlist_id == Wishlist.id)
        .filter(
            Wishlist.user_id == user_id,
            Wishlist.is_public.is_(True),
        )
    )
    return total_lists, total_movies


def _rated_movie_summary(review):
    if not review:
        return None

    return {
        "movieId": review.filme_id,
        "title": review.filme_titulo,
        "posterUrl": review.poster_url,
        "rating": review.nota or 0,
    }


def _highest_rated_movie(user_id):
    review = (
        Review.query.filter(Review.user_id == user_id, Review.nota > 0)
        .order_by(Review.nota.desc(), Review.created_at.desc(), Review.id.desc())
        .first()
    )
    return _rated_movie_summary(review)


def _lowest_rated_movie(user_id):
    review = (
        Review.query.filter(Review.user_id == user_id, Review.nota > 0)
        .order_by(Review.nota.asc(), Review.created_at.desc(), Review.id.desc())
        .first()
    )
    return _rated_movie_summary(review)


def _unique_review_movies(user_id):
    reviews = (
        Review.query.options(
            load_only(
                Review.id,
                Review.filme_id,
                Review.filme_titulo,
                Review.generos,
                Review.ano_lancamento,
                Review.created_at,
                Review.updated_at,
            )
        )
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc(), Review.updated_at.desc(), Review.id.desc())
        .all()
    )

    reviews_by_movie = {}
    for review in reviews:
        key = _movie_key(review)
        if not key:
            continue

        existing = reviews_by_movie.get(key)
        if not existing or (not _parse_genres(existing.generos) and _parse_genres(review.generos)):
            reviews_by_movie[key] = review

    return list(reviews_by_movie.values())


def _resolve_review_genres(review):
    genres = _parse_genres(review.generos)
    if genres:
        return genres

    try:
        metadata = resolver_metadados_filme(movie_id=review.filme_id, title=review.filme_titulo)
    except Exception:
        return []

    return _parse_genres(metadata.get("generos"))


def _top_genres(user_id, limit=TOP_GENRES_LIMIT):
    genre_counts = Counter()

    for review in _unique_review_movies(user_id):
        genres = _resolve_review_genres(review)
        for genre in dict.fromkeys(genres):
            genre_counts[genre] += 1

    ordered_genres = sorted(genre_counts.items(), key=lambda item: (-item[1], item[0].lower()))
    return [
        {"genre": genre, "count": count}
        for genre, count in ordered_genres[:limit]
    ]


def get_public_user_statistics(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return None

    total_watched = _count_distinct_watched_movies(user.id)
    average_rating = _average_rating(user.id)
    top_genres = _top_genres(user.id)
    watched_by_year = _watched_by_year(user.id)
    total_reviews = _scalar_count(db.session.query(func.count(Review.id)).filter(Review.user_id == user.id))
    total_ratings = _rating_count(user.id)
    total_lists, total_movies_in_lists = _public_list_counts(user.id)

    return {
        "userId": user.id,
        "totalWatched": total_watched,
        "averageRating": average_rating,
        "ratingScale": RATING_SCALE,
        "topGenres": top_genres,
        "watchedByYear": watched_by_year,
        "totalReviews": total_reviews,
        "totalRatings": total_ratings,
        "totalLists": total_lists,
        "totalMoviesInLists": total_movies_in_lists,
        "favoriteGenre": top_genres[0]["genre"] if top_genres else None,
        "highestRatedMovie": _highest_rated_movie(user.id),
        "lowestRatedMovie": _lowest_rated_movie(user.id),
        "hasMovieHistory": bool(total_watched or total_ratings or top_genres or watched_by_year),
        "definitions": {
            "watched": "Filmes com resenha registrada pelo usuario.",
            "averageRating": "Media das notas maiores que zero na escala do projeto.",
            "watchedByYear": "Ano em que a primeira resenha do filme foi registrada.",
            "lists": "Somente listas publicas aparecem nestas estatisticas.",
        },
    }
