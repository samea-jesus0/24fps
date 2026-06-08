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

<<<<<<< Updated upstream
=======
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    preparer = db.engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table_name)

    alter_statements = []
    if "display_name" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN display_name VARCHAR(100) NULL")
    if "bio" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN bio TEXT NULL")
    if "foto_pos_x" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN foto_pos_x INTEGER NOT NULL DEFAULT 50")
    if "foto_pos_y" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN foto_pos_y INTEGER NOT NULL DEFAULT 50")
    if "created_at" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN created_at DATETIME NULL")

    if not alter_statements:
        return

    with db.engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))

        if "created_at" not in existing_columns:
            connection.execute(text(f"UPDATE {quoted_table} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))


def ensure_review_columns():
    from models.review import Review

    inspector = inspect(db.engine)
    table_name = Review.__tablename__

    if table_name not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    preparer = db.engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table_name)

    alter_statements = []
    if "filme_id" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN filme_id VARCHAR(100) NULL")
    if "poster_url" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN poster_url VARCHAR(500) NULL")
    if "created_at" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN created_at DATETIME NULL")
    if "updated_at" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN updated_at DATETIME NULL")

    if not alter_statements:
        return

    with db.engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))

        # Preenche colunas novas em registros antigos para manter a tela /perfil funcional.
        if "created_at" not in existing_columns:
            connection.execute(text(f"UPDATE {quoted_table} SET created_at = NOW() WHERE created_at IS NULL"))
        if "updated_at" not in existing_columns:
            connection.execute(text(f"UPDATE {quoted_table} SET updated_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL"))
>>>>>>> Stashed changes

def create_app():
    app = Flask(__name__)

    # 🔥 mantém sua lógica original
    app.config.from_object(Config)

<<<<<<< Updated upstream
    # 🔹 configs extras (caso não estejam no Config)
=======
    db.init_app(app)
    

    from controller.filme_controller import movie_bp
    from controller.perfil_controller import perfil_bp
    from controller.auth_controller import auth
    from controller.catalogo_controller import catalogo_bp
    from controller.dashboard_controller import main
    from controller.user_profile_controller import users_bp
    app.register_blueprint(movie_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(auth)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(main)
    app.register_blueprint(users_bp)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
>>>>>>> Stashed changes
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