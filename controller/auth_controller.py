from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.user import User
from flask_login import login_user, logout_user, login_required
import os
import uuid
from extensions import db, login_manager

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@auth.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])

        # Verifica se já existe
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado')
            return redirect(url_for('auth.login'))

        foto_nome = 'default.png'

        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1]
                filename = f"{uuid.uuid4()}.{ext}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(caminho)
                foto_nome = filename

        user = User(nome=nome, email=email, senha=senha, foto=foto_nome)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('login.html')


# 🔹 LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login inválido')

    return render_template('login.html')


# 🔹 LOGOUT
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))