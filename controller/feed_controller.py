from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from service.feed_service import get_following_feed


feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/feed")
@login_required
def feed():
    return render_template("feed.html")


@feed_bp.route("/api/feed")
@login_required
def feed_api():
    activities = get_following_feed(current_user.id)
    return jsonify(
        {
            "activities": activities,
            "count": len(activities),
        }
    )
