from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


def register_user(nome, email, senha, foto):
    # verifica se já existe
    if User.query.filter_by(email=email).first():
        return None, "Email já cadastrado"

    senha_hash = generate_password_hash(senha)

    user = User(
        nome=nome,
        email=email,
        senha=senha_hash,
        foto=foto
    )

    db.session.add(user)
    db.session.commit()

    return user, None


def login_user_service(email, senha):
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "Usuário não encontrado"

    if not check_password_hash(user.senha, senha):
        return None, "Senha inválida"

    return user, None