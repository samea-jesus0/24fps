from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from extensions import db
from models.review import Review
from service.wishlist_service import list_user_wishlists
import os
import uuid

main = Blueprint("main", __name__)
DEFAULT_AVATAR = "default-avatar.svg"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def normalize_photo_position(value):
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 50


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        file = request.files.get("foto")
        foto_pos_x = normalize_photo_position(request.form.get("foto_pos_x", current_user.foto_pos_x or 50))
        foto_pos_y = normalize_photo_position(request.form.get("foto_pos_y", current_user.foto_pos_y or 50))
        updated_photo = False

        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Formato invalido. Use png, jpg, jpeg ou gif.")
                return redirect(url_for("main.dashboard"))

            if current_user.foto and current_user.foto not in {"default.png", DEFAULT_AVATAR}:
                old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], current_user.foto)
                if os.path.exists(old_path):
                    os.remove(old_path)

            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            caminho = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(caminho)

            current_user.foto = filename
            updated_photo = True

        current_user.foto_pos_x = foto_pos_x
        current_user.foto_pos_y = foto_pos_y
        db.session.commit()

        if updated_photo:
            flash("Foto e enquadramento atualizados com sucesso.")
        else:
            flash("Enquadramento atualizado com sucesso.")
        return redirect(url_for("main.dashboard"))

    reviews = (
        Review.query.filter_by(user_id=current_user.id)
        .order_by(Review.updated_at.desc(), Review.created_at.desc())
        .all()
    )
    wishlists = list_user_wishlists(current_user.id)
    return render_template("perfil.html", user=current_user, reviews=reviews, wishlists=wishlists)
