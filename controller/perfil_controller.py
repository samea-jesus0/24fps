
from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.pesquisa import Search
from service.filme_service import buscar_filme_por_nome
from flask_login import login_required, current_user

perfil_bp = Blueprint("perfil", __name__)

@perfil_bp.route('/perfil')
@login_required
def perfil():
    return render_template("perfil.html", user=current_user)