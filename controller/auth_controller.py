from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from flask_login import login_user, logout_user, login_required, current_user
import os
import uuid
from extensions import db, login_manager

auth = Blueprint("auth", __name__)
DEFAULT_AVATAR = "default-avatar.svg"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def normalize_photo_position(value):
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 50


@auth.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("movie.index"))
    return redirect(url_for("auth.login"))


@auth.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("movie.index"))

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        foto_pos_x = normalize_photo_position(request.form.get("foto_pos_x", 50))
        foto_pos_y = normalize_photo_position(request.form.get("foto_pos_y", 50))

        if User.query.filter_by(email=email).first():
            flash("Email ja cadastrado")
            return redirect(url_for("auth.register"))

        foto_nome = DEFAULT_AVATAR

        if "foto" in request.files:
            file = request.files["foto"]
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Formato invalido. Use png, jpg, jpeg ou gif.")
                    return redirect(url_for("auth.register"))

                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                caminho = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(caminho)
                foto_nome = filename

        user = User(
            nome=nome,
            email=email,
            senha=senha,
            foto=foto_nome,
            foto_pos_x=foto_pos_x,
            foto_pos_y=foto_pos_y,
        )
        db.session.add(user)
        db.session.commit()

        flash("Cadastro realizado com sucesso. Entre para continuar.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("movie.index"))

    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for("movie.index"))

        flash("Login invalido")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
