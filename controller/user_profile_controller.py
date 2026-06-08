from flask import Blueprint, jsonify, render_template, request

from service.user_profile_service import get_public_user_profile, search_public_users


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


@users_bp.route("/users/<int:user_id>")
def public_profile(user_id):
    wants_json = _wants_json_response()
    profile = get_public_user_profile(user_id, external_urls=not wants_json)

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
    profile = get_public_user_profile(user_id)
    if not profile:
        return jsonify({"erro": "Usuario nao encontrado"}), 404
    return jsonify(profile)


@users_bp.route("/api/users")
def users_search_api():
    users = search_public_users(request.args.get("search") or request.args.get("q"))
    return jsonify({"users": users})
