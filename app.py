from flask import Flask
from dotenv import load_dotenv
from config import Config
from extensions import db, login_manager
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    

    from controller.filme_controller import movie_bp
    from controller.perfil_controller import perfil_bp
    from controller.auth_controller import auth
    from controller.dashboard_controller import main
    app.register_blueprint(movie_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(auth)
    app.register_blueprint(main)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    

    with app.app_context():
        from models.pesquisa import Search
        db.create_all()
        
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)