import os
import unittest
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash

from app import app as default_app, create_app
from extensions import db
from models.review import Review
from models.user import User
from models.user_follow import UserFollow
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie


class FeedTestCase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with default_app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
            }
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.viewer = self._create_user("Viewer", "viewer@example.com")
            self.followed = self._create_user("Joao", "joao@example.com")
            self.not_followed = self._create_user("Maria", "maria@example.com")

            db.session.add(
                UserFollow(
                    follower_user_id=self.viewer.id,
                    followed_user_id=self.followed.id,
                )
            )

            review = Review(
                user_id=self.followed.id,
                filme_id="tt0111161",
                filme_titulo="Dune",
                conteudo="Uma resenha de teste.",
                nota=5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(review)

            public_list = Wishlist(
                user_id=self.followed.id,
                titulo="Quero assistir",
                descricao="Filmes para ver depois.",
                is_public=True,
            )
            private_list = Wishlist(
                user_id=self.followed.id,
                titulo="Privada",
                is_public=False,
            )
            db.session.add_all([public_list, private_list])
            db.session.flush()

            db.session.add_all(
                [
                    WishlistMovie(
                        wishlist_id=public_list.id,
                        movie_key="imdb:tt1877830",
                        filme_id="tt1877830",
                        filme_titulo="The Batman",
                        added_at=datetime.utcnow() + timedelta(seconds=1),
                    ),
                    WishlistMovie(
                        wishlist_id=private_list.id,
                        movie_key="imdb:tt9999999",
                        filme_id="tt9999999",
                        filme_titulo="Filme privado",
                        added_at=datetime.utcnow() + timedelta(seconds=2),
                    ),
                    Review(
                        user_id=self.not_followed.id,
                        filme_id="tt9999998",
                        filme_titulo="Filme da Maria",
                        conteudo="Nao deve aparecer.",
                        nota=4,
                        created_at=datetime.utcnow() + timedelta(seconds=3),
                        updated_at=datetime.utcnow() + timedelta(seconds=3),
                    ),
                ]
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    @staticmethod
    def _create_user(name, email):
        user = User(
            nome=name,
            display_name=name,
            email=email,
            senha=generate_password_hash("senha-segura"),
        )
        db.session.add(user)
        db.session.flush()
        return user

    def _logged_client(self):
        client = self.app.test_client()
        response = client.post(
            "/login",
            data={"email": "viewer@example.com", "senha": "senha-segura"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"].split("?")[0], "/feed")
        return client

    def test_feed_requires_authentication(self):
        response = self.app.test_client().get("/api/feed")
        self.assertEqual(response.status_code, 401)

    def test_feed_contains_followed_activities_and_hides_private_and_unfollowed(self):
        client = self._logged_client()
        response = client.get("/api/feed")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        texts = [activity["text"] for activity in payload["activities"]]

        self.assertTrue(any("Joao avaliou Dune com 5 estrelas." in text for text in texts))
        self.assertTrue(any("Joao publicou uma resenha de Dune." in text for text in texts))
        self.assertTrue(any('Joao adicionou The Batman à lista "Quero assistir".' in text for text in texts))
        self.assertFalse(any("Filme privado" in text for text in texts))
        self.assertFalse(any("Maria" in text for text in texts))

    def test_feed_page_is_available_after_login(self):
        client = self._logged_client()
        response = client.get("/feed")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Feed de atividades", response.data)


if __name__ == "__main__":
    unittest.main()
