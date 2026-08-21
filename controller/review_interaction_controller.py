from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from service.review_interaction_service import (
    create_comment,
    create_like,
    get_review,
    get_review_interactions,
    list_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    remove_like,
)


interactions_bp = Blueprint("interactions", __name__)


@interactions_bp.route("/api/reviews/<int:review_id>/interactions")
def review_interactions(review_id):
    viewer_user_id = current_user.id if current_user.is_authenticated else None
    payload = get_review_interactions(review_id, viewer_user_id)
    if not payload:
        return jsonify({"erro": "Resenha nao encontrada."}), 404
    return jsonify(payload)


@interactions_bp.route("/api/reviews/<int:review_id>/likes", methods=["POST"])
@login_required
def like_review(review_id):
    payload, error, status_code = create_like(review_id, current_user.id)
    if error:
        return jsonify({"erro": error}), status_code
    return jsonify(payload), status_code


@interactions_bp.route("/api/reviews/<int:review_id>/likes", methods=["DELETE"])
@login_required
def unlike_review(review_id):
    payload, error, status_code = remove_like(review_id, current_user.id)
    if error:
        return jsonify({"erro": error}), status_code
    return jsonify(payload), status_code


@interactions_bp.route("/api/reviews/<int:review_id>/comments", methods=["GET"])
def get_review_comments(review_id):
    viewer_user_id = current_user.id if current_user.is_authenticated else None
    payload = get_review_interactions(review_id, viewer_user_id)
    if not payload:
        return jsonify({"erro": "Resenha nao encontrada."}), 404
    return jsonify({"comments": payload["comments"], "commentCount": payload["commentCount"]})


@interactions_bp.route("/api/reviews/<int:review_id>/comments", methods=["POST"])
@login_required
def add_review_comment(review_id):
    data = request.get_json(silent=True) or {}
    comment, error, status_code = create_comment(review_id, current_user.id, data.get("content"))
    if error:
        return jsonify({"erro": error}), status_code
    return jsonify(comment), status_code


@interactions_bp.route("/api/notifications")
@login_required
def notifications():
    return jsonify(list_notifications(current_user.id, request.args.get("limit")))


@interactions_bp.route("/api/notifications/read", methods=["POST"])
@login_required
def read_all_notifications():
    return jsonify(mark_all_notifications_as_read(current_user.id))


@interactions_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def read_notification(notification_id):
    notification = mark_notification_as_read(notification_id, current_user.id)
    if not notification:
        return jsonify({"erro": "Notificacao nao encontrada."}), 404
    return jsonify({"id": notification.id, "isRead": True})


@interactions_bp.route("/reviews/<int:review_id>")
def review_detail(review_id):
    review = get_review(review_id)
    if not review:
        return jsonify({"erro": "Resenha nao encontrada."}), 404

    comment_id = request.args.get("comment", type=int)
    target_url = url_for(
        "users.public_profile",
        user_id=review.user_id,
        review=review.id,
        comment=comment_id,
    )
    return redirect(f"{target_url}#review-{review.id}")
