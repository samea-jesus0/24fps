from datetime import datetime

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from models.review import Review
from service.filme_service import buscar_filme_por_nome
from flask_login import login_required, current_user

perfil_bp = Blueprint("perfil", __name__)


def _review_payload(review):
    return {
        "id": review.id,
        "filme_id": review.filme_id,
        "filme_titulo": review.filme_titulo,
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
    return render_template("perfil.html", user=current_user, reviews=reviews)


@perfil_bp.route('/perfil/reviews', methods=['POST'])
@login_required
def create_review():
    data = request.get_json(silent=True) or {}
    filme_titulo = (data.get("filme_titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    filme_id = (data.get("filme_id") or "").strip() or None

    try:
        nota = int(data.get("nota", 0))
    except (TypeError, ValueError):
        nota = 0

    if not filme_titulo or not conteudo:
        return jsonify({"erro": "Preencha o título do filme e a resenha."}), 400

    if nota < 0 or nota > 5:
        return jsonify({"erro": "A nota deve ser entre 0 e 5."}), 400

    review = Review(
        user_id=current_user.id,
        filme_id=filme_id,
        filme_titulo=filme_titulo,
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

    try:
        nota = int(data.get("nota", 0))
    except (TypeError, ValueError):
        nota = 0

    if not filme_titulo or not conteudo:
        return jsonify({"erro": "Preencha o título do filme e a resenha."}), 400

    if nota < 0 or nota > 5:
        return jsonify({"erro": "A nota deve ser entre 0 e 5."}), 400

    review.filme_titulo = filme_titulo
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
