
from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from service.filme_service import buscar_filme_por_nome

resenha_bp = Blueprint("resenha", __name__)

@resenha_bp.route("/resenha")
def resenha():
    return render_template("resenha.html")