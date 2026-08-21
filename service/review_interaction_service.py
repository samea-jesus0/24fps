from datetime import datetime

from flask import url_for
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.notification import Notification
from models.review import Review
from models.review_comment import ReviewComment
from models.review_like import ReviewLike


DEFAULT_AVATAR = "default-avatar.svg"
MAX_COMMENT_LENGTH = 1200
NOTIFICATION_LIMIT = 30


def _display_name(user):
    return (user.display_name or user.nome or f"Usuario {user.id}").strip()


def _avatar_url(user):
    filename = user.foto if user.foto and user.foto != "default.png" else DEFAULT_AVATAR
    return url_for("static", filename=f"uploads/{filename}")


def _isoformat(value):
    return value.isoformat() if value else None


def _comment_payload(comment):
    return {
        "id": comment.id,
        "reviewId": comment.review_id,
        "content": comment.conteudo,
        "createdAt": _isoformat(comment.created_at),
        "updatedAt": _isoformat(comment.updated_at),
        "user": {
            "id": comment.user.id,
            "displayName": _display_name(comment.user),
            "avatarUrl": _avatar_url(comment.user),
            "avatarPosition": {
                "x": comment.user.foto_pos_x or 50,
                "y": comment.user.foto_pos_y or 50,
            },
        },
    }


def _notification_payload(notification):
    movie_title = notification.review.filme_titulo if notification.review else "uma resenha"
    actor_name = _display_name(notification.actor)
    action = "curtiu" if notification.type == "like" else "comentou em"

    return {
        "id": notification.id,
        "type": notification.type,
        "isRead": notification.is_read,
        "createdAt": _isoformat(notification.created_at),
        "actor": {
            "id": notification.actor.id,
            "displayName": actor_name,
            "avatarUrl": _avatar_url(notification.actor),
            "avatarPosition": {
                "x": notification.actor.foto_pos_x or 50,
                "y": notification.actor.foto_pos_y or 50,
            },
        },
        "review": {
            "id": notification.review_id,
            "movieTitle": movie_title,
        },
        "commentId": notification.comment_id,
        "message": f"{actor_name} {action} sua resenha sobre {movie_title}.",
        "targetUrl": url_for(
            "interactions.review_detail",
            review_id=notification.review_id,
            comment=notification.comment_id,
        ),
    }


def get_review(review_id):
    return db.session.get(Review, review_id)


def get_review_interactions(review_id, viewer_user_id=None):
    review = get_review(review_id)
    if not review:
        return None

    likes_query = ReviewLike.query.filter_by(review_id=review.id)
    comments = (
        ReviewComment.query.filter_by(review_id=review.id)
        .order_by(ReviewComment.created_at.asc(), ReviewComment.id.asc())
        .all()
    )
    liked_by_current_user = False
    if viewer_user_id:
        liked_by_current_user = likes_query.filter_by(user_id=viewer_user_id).first() is not None

    return {
        "reviewId": review.id,
        "likeCount": likes_query.count(),
        "commentCount": len(comments),
        "likedByCurrentUser": liked_by_current_user,
        "comments": [_comment_payload(comment) for comment in comments],
    }


def _create_notification(notification_type, recipient_user_id, actor_user_id, review_id, comment_id=None):
    if recipient_user_id == actor_user_id:
        return None

    notification = Notification(
        recipient_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
        review_id=review_id,
        comment_id=comment_id,
        type=notification_type,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.session.add(notification)
    return notification


def create_like(review_id, user_id):
    review = get_review(review_id)
    if not review:
        return None, "Resenha nao encontrada.", 404

    if ReviewLike.query.filter_by(review_id=review.id, user_id=user_id).first():
        return None, "Voce ja curtiu esta resenha.", 409

    like = ReviewLike(review_id=review.id, user_id=user_id, created_at=datetime.utcnow())
    db.session.add(like)
    _create_notification("like", review.user_id, user_id, review.id)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "Voce ja curtiu esta resenha.", 409

    return get_review_interactions(review.id, user_id), None, 201


def remove_like(review_id, user_id):
    review = get_review(review_id)
    if not review:
        return None, "Resenha nao encontrada.", 404

    like = ReviewLike.query.filter_by(review_id=review.id, user_id=user_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()

    return get_review_interactions(review.id, user_id), None, 200


def create_comment(review_id, user_id, content):
    review = get_review(review_id)
    if not review:
        return None, "Resenha nao encontrada.", 404

    if not isinstance(content, str):
        return None, "O comentario precisa conter texto.", 400

    content = content.strip()
    if not content:
        return None, "O comentario nao pode estar vazio.", 400
    if len(content) > MAX_COMMENT_LENGTH:
        return None, f"O comentario deve ter no maximo {MAX_COMMENT_LENGTH} caracteres.", 400

    comment = ReviewComment(
        review_id=review.id,
        user_id=user_id,
        conteudo=content,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(comment)
    db.session.flush()
    _create_notification("comment", review.user_id, user_id, review.id, comment.id)
    db.session.commit()

    return _comment_payload(comment), None, 201


def list_notifications(user_id, limit=NOTIFICATION_LIMIT):
    try:
        limit = int(limit or NOTIFICATION_LIMIT)
    except (TypeError, ValueError):
        limit = NOTIFICATION_LIMIT
    limit = max(1, min(limit, 50))
    notifications = (
        Notification.query.filter_by(recipient_user_id=user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )
    unread_count = Notification.query.filter_by(recipient_user_id=user_id, is_read=False).count()
    return {
        "notifications": [_notification_payload(notification) for notification in notifications],
        "unreadCount": unread_count,
    }


def mark_all_notifications_as_read(user_id):
    Notification.query.filter_by(recipient_user_id=user_id, is_read=False).update(
        {Notification.is_read: True}, synchronize_session=False
    )
    db.session.commit()
    return {"unreadCount": 0}


def mark_notification_as_read(notification_id, user_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_user_id=user_id,
    ).first()
    if not notification:
        return None

    if not notification.is_read:
        notification.is_read = True
        db.session.commit()

    return notification
