from sqlalchemy.orm import load_only

from models.review import Review
from service.user_statistics_service import _movie_key_from_values, _parse_genres


MINIMUM_RATINGS = 5
RANKING_LIMIT = 5


def get_movie_ranking():
    """Return the five highest-rated movies using only metadata stored on reviews.

    A single, narrow query loads valid reviews. Python groups the rows by the same
    IMDb-ID/title-fallback key used by profile statistics, which also handles IDs
    and titles whose casing or surrounding whitespace differs.
    """
    reviews = (
        Review.query.options(
            load_only(
                Review.id,
                Review.user_id,
                Review.filme_id,
                Review.filme_titulo,
                Review.poster_url,
                Review.generos,
                Review.ano_lancamento,
                Review.nota,
                Review.updated_at,
            )
        )
        .filter(Review.nota > 0)
        .order_by(Review.updated_at.desc(), Review.id.desc())
        .all()
    )

    movies = {}
    for review in reviews:
        movie_key = _movie_key_from_values(review.filme_id, review.filme_titulo)
        if movie_key == "title:":
            continue

        movie = movies.setdefault(
            movie_key,
            {
                "movieId": (review.filme_id or "").strip().lower() or None,
                "title": (review.filme_titulo or "").strip(),
                "poster": None,
                "year": None,
                "genres": [],
                "ratingTotal": 0,
                "ratingCount": 0,
                "raterIds": set(),
            },
        )
        movie["ratingTotal"] += review.nota
        movie["ratingCount"] += 1
        movie["raterIds"].add(review.user_id)

        if not movie["poster"] and review.poster_url:
            movie["poster"] = review.poster_url.strip() or None
        if movie["year"] is None and review.ano_lancamento:
            movie["year"] = review.ano_lancamento
        if not movie["genres"] and review.generos:
            movie["genres"] = _parse_genres(review.generos)

    eligible_movies = []
    for movie_key, movie in movies.items():
        rater_count = len(movie["raterIds"])
        if rater_count < MINIMUM_RATINGS:
            continue

        movie["average"] = movie["ratingTotal"] / movie["ratingCount"]
        movie["raterCount"] = rater_count
        movie["movieKey"] = movie_key
        eligible_movies.append(movie)

    eligible_movies.sort(
        key=lambda movie: (
            -movie["average"],
            -movie["ratingCount"],
            -movie["raterCount"],
            movie["title"].casefold(),
            movie["movieKey"],
        )
    )

    return [
        {
            "position": position,
            "movieId": movie["movieId"],
            "title": movie["title"],
            "poster": movie["poster"],
            "averageRating": round(movie["average"], 1),
            "ratingCount": movie["ratingCount"],
            "year": movie["year"],
            "genres": movie["genres"],
        }
        for position, movie in enumerate(eligible_movies[:RANKING_LIMIT], start=1)
    ]
