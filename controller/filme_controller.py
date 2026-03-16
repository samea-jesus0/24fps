from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from service.filme_service import buscar_filme_por_nome

movie_bp = Blueprint("movie", __name__)

@movie_bp.route("/")
def index():
    return render_template("index.html")

@movie_bp.route("/buscar", methods=["POST"])
def buscar():
    nome_filme = request.json.get("nome")

    if not nome_filme:
        return jsonify({"erro": "Digite o nome de um filme"}), 400

    nova_busca = Search(movie_name=nome_filme)
    db.session.add(nova_busca)
    db.session.commit()

    filme = buscar_filme_por_nome(nome_filme)

    if not filme:
        return jsonify({"erro": "Filme não encontrado"}), 404

    return jsonify(filme)