from flask import render_template, request, redirect, url_for, flash, current_app
from services.auth_service import register_user
from . import auth
import os
import uuid


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        foto_nome = 'default.png'

        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(caminho)
                foto_nome = filename

        user, erro = register_user(nome, email, senha, foto_nome)

        if erro:
            flash(erro)
            return redirect(url_for('auth.register'))

        return redirect(url_for('auth.login'))

    return render_template('register.html')