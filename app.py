from flask import Flask
from dotenv import load_dotenv
from config import Config
from extensions import db, login_manager
from sqlalchemy import inspect, text
import os

load_dotenv()


def ensure_user_avatar_columns():
    from models.user import User

    inspector = inspect(db.engine)
    table_name = User.__tablename__

    if table_name not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    preparer = db.engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table_name)

    alter_statements = []
    if "foto_pos_x" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN foto_pos_x INTEGER NOT NULL DEFAULT 50")
    if "foto_pos_y" not in existing_columns:
        alter_statements.append(f"ALTER TABLE {quoted_table} ADD COLUMN foto_pos_y INTEGER NOT NULL DEFAULT 50")

    if not alter_statements:
        return

    with db.engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    

    from controller.filme_controller import movie_bp
    from controller.perfil_controller import perfil_bp
    from controller.auth_controller import auth
    from controller.catalogo_controller import catalogo_bp
    from controller.dashboard_controller import main
    app.register_blueprint(movie_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(auth)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(main)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    

    with app.app_context():
        from models.user import User
        from models.pesquisa import Search
        from models.review import Review

        db.create_all()
        ensure_user_avatar_columns()
        
    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
