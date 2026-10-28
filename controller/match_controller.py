from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from service.match_service import get_match_details, get_match_page_data, get_user_matches


matches_bp = Blueprint("matches", __name__)


@matches_bp.route("/matches")
@login_required
def match_page():
    page_data = get_match_page_data(current_user.id)
    return render_template(
        "matches.html",
        matches=page_data["matches"],
        has_history=page_data["hasHistory"],
    )


@matches_bp.route("/matches/<int:user_id>")
@login_required
def match_detail(user_id):
    if current_user.id == user_id:
        return render_template("match_detail.html", match=None, error="Este perfil é o seu."), 404

    match = get_match_details(current_user.id, user_id)
    if not match:
        return render_template("match_detail.html", match=None, error="Usuário não encontrado."), 404
    return render_template("match_detail.html", match=match, error=None)


@matches_bp.route("/api/matches")
def matches_api():
    if not current_user.is_authenticated:
        return jsonify({"erro": "Autenticação requerida."}), 401
    return jsonify({"matches": get_user_matches(current_user.id)})


@matches_bp.route("/api/matches/<int:user_id>")
def match_details_api(user_id):
    if not current_user.is_authenticated:
        return jsonify({"erro": "Autenticação requerida."}), 401
    if current_user.id == user_id:
        return jsonify({"erro": "Não é possível calcular compatibilidade com o próprio perfil."}), 400

    match = get_match_details(current_user.id, user_id)
    if not match:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(match)
