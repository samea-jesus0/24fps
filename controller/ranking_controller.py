from flask import Blueprint, jsonify, render_template

from service.movie_ranking_service import MINIMUM_RATINGS, get_movie_ranking


ranking_bp = Blueprint("ranking", __name__)


@ranking_bp.route("/ranking")
def ranking_page():
    return render_template("ranking.html")


@ranking_bp.route("/api/ranking")
def ranking_api():
    ranking = get_movie_ranking()
    return jsonify(
        {
            "ranking": ranking,
            "minimumRatings": MINIMUM_RATINGS,
            "totalMovies": len(ranking),
        }
    )
