from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from service.filme_service import buscar_filme_por_id, buscar_filme_por_nome

movie_bp = Blueprint("movie", __name__)

@movie_bp.route("/pesquisa")
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


@movie_bp.route("/sugestoes", methods=["GET"])
def sugestoes():
    query = request.args.get("q", "").strip()

    if not query or len(query) < 2:
        return jsonify([])

    try:
        from service.filme_service import buscar_sugestoes_filmes
        sugestoes = buscar_sugestoes_filmes(query)
        return jsonify(sugestoes[:10])  # Limita a 10 sugestões
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@movie_bp.route("/api/movies/details", methods=["GET"])
def movie_details():
    imdb_id = (request.args.get("imdb_id") or "").strip()
    titulo = (request.args.get("titulo") or request.args.get("nome") or "").strip()

    if not imdb_id and not titulo:
        return jsonify({"erro": "Informe um imdb_id ou titulo do filme."}), 400

    try:
        filme = buscar_filme_por_id(imdb_id) if imdb_id else buscar_filme_por_nome(titulo)
        if not filme and imdb_id and titulo:
            filme = buscar_filme_por_nome(titulo)
    except RuntimeError as exc:
        return jsonify({"erro": str(exc)}), 503
    except Exception:
        return jsonify({"erro": "Nao foi possivel carregar os detalhes do filme agora."}), 500

    if not filme:
        return jsonify({"erro": "Filme nao encontrado"}), 404

    return jsonify(filme)


