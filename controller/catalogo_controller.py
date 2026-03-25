
from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from service.filme_service import buscar_filme_por_nome

catalogo_bp = Blueprint("catalogo", __name__)

@catalogo_bp.route("/catalogo")
def catalogo():
    return render_template("catalogo.html")