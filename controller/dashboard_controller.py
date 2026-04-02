from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
import os
import uuid

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':

        if 'foto' in request.files:
            file = request.files['foto']

            if file and allowed_file(file.filename):

                # 🔥 Remove foto antiga
                if current_user.foto and current_user.foto != 'default.png':
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.foto)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # 🔥 Gera nome único
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"

                # 🔥 Salva arquivo
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(caminho)

                # 🔥 ATUALIZA no banco (ESSA É A CHAVE)
                current_user.foto = filename
                db.session.commit()

        return redirect(url_for('main.dashboard'))

    return render_template('perfil.html', user=current_user)