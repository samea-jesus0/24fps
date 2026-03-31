from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user
from services.auth_service import login_user_service
from . import auth


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        user, erro = login_user_service(email, senha)

        if erro:
            flash(erro)
            return redirect(url_for('auth.login'))

        login_user(user)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')