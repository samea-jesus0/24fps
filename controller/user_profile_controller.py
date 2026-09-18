from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from models.user import User
from models.user_follow import UserFollow
from service.user_profile_service import (
    count_followers,
    count_following,
    get_public_user_profile,
    is_following,
    list_followers,
    list_following,
    list_public_users,
    search_public_users,
)
from service.user_statistics_service import get_public_user_statistics
from extensions import db


users_bp = Blueprint("users", __name__)


def _wants_json_response():
    if request.args.get("format") == "json":
        return True

    best_match = request.accept_mimetypes.best_match(["text/html", "application/json"])
    return best_match == "application/json" and (
        request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]
    )


def _profile_not_found_response(wants_json):
    if wants_json:
        return jsonify({"erro": "Usuario nao encontrado"}), 404

    return (
        render_template(
            "user_profile.html",
            state="not_found",
            profile=None,
            meta={
                "title": "Perfil nao encontrado | 24FPS",
                "description": "O perfil solicitado nao foi encontrado no 24FPS.",
                "image": None,
            },
        ),
        404,
    )


def _optional_positive_int(value):
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None
    return parsed_value if parsed_value > 0 else None


@users_bp.route("/users")
def directory():
    wants_json = _wants_json_response()
    query = (request.args.get("search") or request.args.get("q") or "").strip()
    exclude_user_id = current_user.id if current_user.is_authenticated else None

    if query:
        users = search_public_users(query, exclude_user_id=exclude_user_id, external_urls=not wants_json)
    else:
        users = list_public_users(exclude_user_id=exclude_user_id, external_urls=not wants_json)

    if wants_json:
        return jsonify(
            {
                "query": query,
                "queryTooShort": 0 < len(query) < 2,
                "users": users,
            }
        )

    title = "Perfis | 24FPS"
    description = "Pesquise outros usuarios do 24FPS e abra perfis publicos."
    if query:
        title = f'Perfis para "{query}" | 24FPS'
        description = f'Resultados da busca por "{query}" no 24FPS.'

    return render_template(
        "user_directory.html",
        query=query,
        query_too_short=0 < len(query) < 2,
        users=users,
        meta={
            "title": title,
            "description": description,
            "image": None,
        },
    )


@users_bp.route("/users/<int:user_id>")
def public_profile(user_id):
    wants_json = _wants_json_response()
    viewer_user_id = current_user.id if current_user.is_authenticated else None
    highlighted_review_id = _optional_positive_int(request.args.get("review"))
    profile = get_public_user_profile(
        user_id,
        external_urls=not wants_json,
        viewer_user_id=viewer_user_id,
        highlighted_review_id=highlighted_review_id,
    )

    if not profile:
        return _profile_not_found_response(wants_json)

    if wants_json:
        return jsonify(profile)

    return render_template(
        "user_profile.html",
        state="success",
        profile=profile,
        meta={
            "title": f"{profile['displayName']} | 24FPS",
            "description": profile["bio"] or f"Perfil publico de {profile['displayName']} no 24FPS.",
            "image": profile["avatarUrl"],
        },
    )


@users_bp.route("/api/users/<int:user_id>")
def public_profile_api(user_id):
    viewer_user_id = current_user.id if current_user.is_authenticated else None
    highlighted_review_id = _optional_positive_int(request.args.get("review"))
    profile = get_public_user_profile(
        user_id,
        viewer_user_id=viewer_user_id,
        highlighted_review_id=highlighted_review_id,
    )
    if not profile:
        return jsonify({"erro": "Usuario nao encontrado"}), 404
    return jsonify(profile)


@users_bp.route("/api/users/<int:user_id>/statistics")
def public_profile_statistics_api(user_id):
    statistics = get_public_user_statistics(user_id)
    if not statistics:
        return jsonify({"erro": "Usuario nao encontrado"}), 404
    return jsonify(statistics)


@users_bp.route("/api/users/<int:user_id>/follow", methods=["POST", "DELETE"])
def toggle_follow(user_id):
    if not current_user.is_authenticated:
        return jsonify({"erro": "Autenticacao requerida."}), 401

    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"erro": "Usuario nao encontrado"}), 404

    if current_user.id == user_id:
        return jsonify({"erro": "Voce nao pode seguir a si mesmo."}), 400

    existing_follow = UserFollow.query.filter_by(
        follower_user_id=current_user.id,
        followed_user_id=user_id,
    ).first()

    if request.method == "POST":
        if existing_follow:
            return jsonify({
                "erro": "Relacao de seguir ja existe.",
                "isFollowing": True,
                "followingCount": count_following(current_user.id),
                "followerCount": count_followers(user_id),
            }), 409

        follow_relation = UserFollow(follower_user_id=current_user.id, followed_user_id=user_id)
        db.session.add(follow_relation)
        db.session.commit()

        payload = {
            "isFollowing": True,
            "followingCount": count_following(current_user.id),
            "followerCount": count_followers(user_id),
            "profileFollowingCount": count_following(user_id),
            "profileFollowerCount": count_followers(user_id),
        }
        return jsonify(payload), 201

    if not existing_follow:
        return jsonify({
            "erro": "Relacionamento nao encontrado.",
            "isFollowing": False,
            "followingCount": count_following(current_user.id),
            "followerCount": count_followers(user_id),
        }), 404

    db.session.delete(existing_follow)
    db.session.commit()

    payload = {
        "isFollowing": False,
        "followingCount": count_following(current_user.id),
        "followerCount": count_followers(user_id),
        "profileFollowingCount": count_following(user_id),
        "profileFollowerCount": count_followers(user_id),
    }
    return jsonify(payload), 200


@users_bp.route("/api/users/<int:user_id>/followers")
def list_followers_api(user_id):
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"erro": "Usuario nao encontrado"}), 404

    users = list_followers(user_id)
    return jsonify({"count": len(users), "users": users})


@users_bp.route("/api/users/<int:user_id>/following")
def list_following_api(user_id):
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"erro": "Usuario nao encontrado"}), 404

    users = list_following(user_id)
    return jsonify({"count": len(users), "users": users})


@users_bp.route("/api/users")
def users_search_api():
    query = (request.args.get("search") or request.args.get("q") or "").strip()
    exclude_user_id = current_user.id if current_user.is_authenticated else None

    if query:
        users = search_public_users(query, exclude_user_id=exclude_user_id)
    else:
        users = list_public_users(exclude_user_id=exclude_user_id)

    return jsonify(
        {
            "query": query,
            "queryTooShort": 0 < len(query) < 2,
            "users": users,
        }
    )
