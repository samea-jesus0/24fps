import requests
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from service.recommendation_service import get_movie_recommendations


recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/api/recommendations")
@login_required
def recommendations_api():
    try:
        recommendations = get_movie_recommendations(
            current_user.id,
            rotation=request.args.get("rotation", 0),
        )
    except requests.RequestException:
        current_app.logger.exception("Falha ao carregar recomendacoes da OMDb.")
        return jsonify({"erro": "Nao foi possivel carregar recomendacoes agora."}), 503
    except RuntimeError:
        current_app.logger.exception("Configuracao da OMDb ausente nas recomendacoes.")
        return jsonify({"erro": "O servico de filmes esta indisponivel no momento."}), 503

    return jsonify({"recommendations": recommendations})
