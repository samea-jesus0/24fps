from flask import Flask
from dotenv import load_dotenv
from config import Config
from extensions import db, login_manager
import os
import pymysql

load_dotenv()


# 🔹 Cria banco automaticamente
def create_database():
    connection = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )

    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")

    cursor.close()
    connection.close()


def create_app():
    app = Flask(__name__)

    # 🔥 mantém sua lógica original
    app.config.from_object(Config)

    # 🔹 configs extras (caso não estejam no Config)
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # 🔹 inicializações
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 🔹 cria pasta upload automaticamente
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 🔹 Blueprints antigos
    from controller.filme_controller import movie_bp
    from controller.perfil_controller import perfil_bp

    app.register_blueprint(movie_bp)
    app.register_blueprint(perfil_bp)

    # 🔹 Blueprints novos (login + dashboard)
    from controller.auth_controller import auth
    from controller.dashboard_controller import main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        create_database()   # 🔥 cria banco
        db.create_all()     # 🔥 cria tabelas

    app.run(debug=True)