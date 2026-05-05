from app import create_app
from models.user import User
from flask_login import login_user
import traceback

app = create_app()
with app.app_context():
    user = User.query.first()
    print('user', user, 'id=', user.id if user else None)
    with app.test_request_context('/perfil'):
        if user:
            login_user(user)
        try:
            from controller.perfil_controller import perfil
            response = perfil()
            print('response type:', type(response))
            print(response)
        except Exception:
            traceback.print_exc()
