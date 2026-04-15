from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from service.filme_service import obter_catalogo_filmes


catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/catalogo")
@login_required
def catalogo():
    return render_template("catalogo.html", user=current_user)


@catalogo_bp.route("/api/catalogo")
@login_required
def catalogo_api():
    payload = obter_catalogo_filmes(request.args)
    status_code = 503 if payload.get("error") else 200
    return jsonify(payload), status_code
