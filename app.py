from flask import Flask
from dotenv import load_dotenv
from config import Config
from extensions import db

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from controller.filme_controller import movie_bp
    from controller.perfil_controller import perfil_bp
    app.register_blueprint(movie_bp)
    app.register_blueprint(perfil_bp)

    with app.app_context():
        from models.pesquisa import Search
        db.create_all()
        
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)