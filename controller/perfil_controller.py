from datetime import datetime

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from models.review import Review
from service.filme_service import buscar_filme_por_nome
from service.wishlist_service import (
    add_movie_to_wishlist,
    create_wishlist as create_wishlist_service,
    delete_wishlist as delete_wishlist_service,
    list_user_wishlists,
    remove_movie_from_wishlist,
    update_wishlist as update_wishlist_service,
)
from flask_login import login_required, current_user

perfil_bp = Blueprint("perfil", __name__)


def _review_payload(review):
    return {
        "id": review.id,
        "filme_id": review.filme_id,
        "filme_titulo": review.filme_titulo,
        "poster_url": review.poster_url,
        "conteudo": review.conteudo,
        "nota": review.nota,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }


@perfil_bp.route('/perfil')
@login_required
def perfil():
    reviews = (
        Review.query.filter_by(user_id=current_user.id)
        .order_by(Review.updated_at.desc(), Review.created_at.desc())
        .all()
    )
    wishlists = list_user_wishlists(current_user.id)
    return render_template("perfil.html", user=current_user, reviews=reviews, wishlists=wishlists)


@perfil_bp.route('/perfil/reviews', methods=['POST'])
@login_required
def create_review():
    data = request.get_json(silent=True) or {}
    filme_titulo = (data.get("filme_titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    filme_id = (data.get("filme_id") or "").strip() or None
    poster_url = (data.get("poster_url") or "").strip() or None

    try:
        nota = int(data.get("nota", 0))
    except (TypeError, ValueError):
        nota = 0

    if not filme_titulo or not conteudo:
        return jsonify({"erro": "Preencha o título do filme e a resenha."}), 400

    if nota < 0 or nota > 5:
        return jsonify({"erro": "A nota deve ser entre 0 e 5."}), 400

    # Se não temos poster_url, tentar buscar do OMDB
    if not poster_url:
        try:
            if filme_id:
                filme_data = buscar_filme_por_nome(filme_id)  # buscar por ID
            else:
                filme_data = buscar_filme_por_nome(filme_titulo)
            if filme_data and filme_data.get("poster"):
                poster_url = filme_data["poster"]
        except Exception:
            pass  # Ignorar erros na busca do poster

    review = Review(
        user_id=current_user.id,
        filme_id=filme_id,
        filme_titulo=filme_titulo,
        poster_url=poster_url,
        conteudo=conteudo,
        nota=nota,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(review)
    db.session.commit()
    return jsonify(_review_payload(review)), 201


@perfil_bp.route('/perfil/reviews/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    review = Review.query.filter_by(id=review_id, user_id=current_user.id).first()
    if not review:
        return jsonify({"erro": "Resenha não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    filme_titulo = (data.get("filme_titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    filme_id = (data.get("filme_id") or "").strip() or None
    poster_url = (data.get("poster_url") or "").strip() or None

    try:
        nota = int(data.get("nota", 0))
    except (TypeError, ValueError):
        nota = 0

    if not filme_titulo or not conteudo:
        return jsonify({"erro": "Preencha o título do filme e a resenha."}), 400

    if nota < 0 or nota > 5:
        return jsonify({"erro": "A nota deve ser entre 0 e 5."}), 400

    # Se não temos poster_url, tentar buscar do OMDB
    if not poster_url:
        try:
            if filme_id:
                filme_data = buscar_filme_por_nome(filme_id)  # buscar por ID
            else:
                filme_data = buscar_filme_por_nome(filme_titulo)
            if filme_data and filme_data.get("poster"):
                poster_url = filme_data["poster"]
        except Exception:
            pass  # Ignorar erros na busca do poster

    review.filme_id = filme_id
    review.filme_titulo = filme_titulo
    review.poster_url = poster_url
    review.conteudo = conteudo
    review.nota = nota
    review.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(_review_payload(review))


@perfil_bp.route('/perfil/reviews/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = Review.query.filter_by(id=review_id, user_id=current_user.id).first()
    if not review:
        return jsonify({"erro": "Resenha não encontrada."}), 404

    db.session.delete(review)
    db.session.commit()
    return jsonify({"success": True})


@perfil_bp.route('/perfil/wishlists', methods=['GET'])
@login_required
def get_wishlists():
    return jsonify({"wishlists": list_user_wishlists(current_user.id)})


@perfil_bp.route('/perfil/wishlists', methods=['POST'])
@login_required
def create_wishlist():
    data = request.get_json(silent=True) or request.form or {}
    title = data.get("title") or data.get("titulo")
    description = data.get("description") or data.get("descricao") or ""
    raw_is_public = data.get("is_public", True)

    if isinstance(raw_is_public, str):
        is_public = raw_is_public.strip().lower() not in {"false", "0", "off", "nao", "não"}
    else:
        is_public = bool(raw_is_public)

    wishlist, error = create_wishlist_service(
        current_user.id,
        title=title,
        description=description,
        is_public=is_public,
    )

    if error:
        return jsonify({"erro": error}), 400

    return jsonify(wishlist), 201


@perfil_bp.route('/perfil/wishlists/<int:wishlist_id>/movies', methods=['POST'])
@login_required
def add_movie(wishlist_id):
    data = request.get_json(silent=True) or request.form or {}
    title = data.get("title") or data.get("movie_title") or data.get("filme_titulo")
    movie_id = data.get("movie_id") or data.get("filme_id")
    poster_url = data.get("poster_url")

    wishlist, error = add_movie_to_wishlist(
        current_user.id,
        wishlist_id=wishlist_id,
        title=title,
        movie_id=movie_id,
        poster_url=poster_url,
    )

    if error:
        status_code = 409 if "ja esta" in error else 400
        return jsonify({"erro": error}), status_code

    return jsonify(wishlist), 201


@perfil_bp.route('/perfil/wishlists/<int:wishlist_id>', methods=['PUT'])
@login_required
def update_wishlist(wishlist_id):
    data = request.get_json(silent=True) or request.form or {}
    title = data.get("title") or data.get("titulo")
    description = data.get("description") or data.get("descricao") or ""
    raw_is_public = data.get("is_public", True)

    if isinstance(raw_is_public, str):
        is_public = raw_is_public.strip().lower() not in {"false", "0", "off", "nao", "não"}
    else:
        is_public = bool(raw_is_public)

    wishlist, error = update_wishlist_service(
        current_user.id,
        wishlist_id=wishlist_id,
        title=title,
        description=description,
        is_public=is_public,
    )

    if error:
        status_code = 404 if "nao encontrada" in error else 400
        return jsonify({"erro": error}), status_code

    return jsonify(wishlist)


@perfil_bp.route('/perfil/wishlists/<int:wishlist_id>', methods=['DELETE'])
@login_required
def delete_wishlist(wishlist_id):
    error = delete_wishlist_service(current_user.id, wishlist_id=wishlist_id)
    if error:
        return jsonify({"erro": error}), 404

    return jsonify({"success": True, "wishlistId": wishlist_id})


@perfil_bp.route('/perfil/wishlists/<int:wishlist_id>/movies/<int:wishlist_movie_id>', methods=['DELETE'])
@login_required
def delete_wishlist_movie(wishlist_id, wishlist_movie_id):
    wishlist, error = remove_movie_from_wishlist(
        current_user.id,
        wishlist_id=wishlist_id,
        wishlist_movie_id=wishlist_movie_id,
    )

    if error:
        status_code = 404 if "nao encontrada" in error or "nao encontrado" in error else 400
        return jsonify({"erro": error}), status_code

    return jsonify(wishlist)
