import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash

from app import app as default_app, create_app
from extensions import db
from models.review import Review
from models.user import User
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie


class UserStatisticsTestCase(unittest.TestCase):
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
        self.owner_email = "cinefila@example.com"
        self.viewer_email = "visitante@example.com"

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            self.owner_id = self._create_user("Cinefila", self.owner_email)
            self.viewer_id = self._create_user("Visitante", self.viewer_email)
            self.empty_user_id = self._create_user("Sem Filmes", "sem-filmes@example.com")

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
        db.session.commit()
        return user.id

    def _logged_client(self, email):
        client = self.app.test_client()
        response = client.post(
            "/login",
            data={"email": email, "senha": "senha-segura"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        return client

    def _seed_profile_history(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    Review(
                        user_id=self.owner_id,
                        filme_id="tt1392190",
                        filme_titulo="Mad Max: Fury Road",
                        poster_url="https://example.com/mad-max.jpg",
                        generos="Action, Action, Sci-Fi",
                        ano_lancamento=2015,
                        conteudo="Energia pura.",
                        nota=5,
                        created_at=datetime(2024, 5, 10, 12, 0, 0),
                    ),
                    Review(
                        user_id=self.owner_id,
                        filme_id="tt2543164",
                        filme_titulo="Arrival",
                        poster_url="https://example.com/arrival.jpg",
                        generos="Drama, Sci-Fi",
                        ano_lancamento=2016,
                        conteudo="Ideia bonita e precisa.",
                        nota=4,
                        created_at=datetime(2024, 7, 4, 12, 0, 0),
                    ),
                    Review(
                        user_id=self.owner_id,
                        filme_id="tt0468492",
                        filme_titulo="The Host",
                        poster_url="https://example.com/host.jpg",
                        generos="Horror",
                        ano_lancamento=2006,
                        conteudo="Sessao divertida.",
                        nota=0,
                        created_at=datetime(2025, 1, 20, 12, 0, 0),
                    ),
                ]
            )

            public_list = Wishlist(
                user_id=self.owner_id,
                titulo="Favoritos publicos",
                is_public=True,
            )
            private_list = Wishlist(
                user_id=self.owner_id,
                titulo="Lista privada",
                is_public=False,
            )
            db.session.add_all([public_list, private_list])
            db.session.flush()

            db.session.add_all(
                [
                    WishlistMovie(
                        wishlist_id=public_list.id,
                        movie_key="imdb:tt1392190",
                        filme_id="tt1392190",
                        filme_titulo="Mad Max: Fury Road",
                    ),
                    WishlistMovie(
                        wishlist_id=public_list.id,
                        movie_key="imdb:tt2543164",
                        filme_id="tt2543164",
                        filme_titulo="Arrival",
                    ),
                    WishlistMovie(
                        wishlist_id=private_list.id,
                        movie_key="imdb:tt0111161",
                        filme_id="tt0111161",
                        filme_titulo="The Shawshank Redemption",
                    ),
                ]
            )
            db.session.commit()

    def test_public_statistics_uses_real_profile_data_without_login(self):
        self._seed_profile_history()

        response = self.app.test_client().get(f"/api/users/{self.owner_id}/statistics")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["totalWatched"], 3)
        self.assertEqual(payload["averageRating"], 4.5)
        self.assertEqual(payload["ratingScale"], 5)
        self.assertEqual(payload["totalReviews"], 3)
        self.assertEqual(payload["totalRatings"], 2)
        self.assertEqual(payload["totalLists"], 1)
        self.assertEqual(payload["totalMoviesInLists"], 2)
        self.assertEqual(payload["favoriteGenre"], "Sci-Fi")
        self.assertEqual(payload["topGenres"][0], {"genre": "Sci-Fi", "count": 2})
        self.assertIn({"genre": "Action", "count": 1}, payload["topGenres"])
        self.assertEqual(
            payload["watchedByYear"],
            [{"year": 2024, "count": 2}, {"year": 2025, "count": 1}],
        )
        self.assertEqual(payload["highestRatedMovie"]["title"], "Mad Max: Fury Road")
        self.assertEqual(payload["lowestRatedMovie"]["title"], "Arrival")
        self.assertTrue(payload["hasMovieHistory"])

    def test_statistics_allows_authenticated_viewer_to_open_another_profile(self):
        self._seed_profile_history()
        client = self._logged_client(self.viewer_email)

        response = client.get(f"/api/users/{self.owner_id}/statistics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["userId"], self.owner_id)

    def test_statistics_for_user_without_watched_movies(self):
        response = self.app.test_client().get(f"/api/users/{self.empty_user_id}/statistics")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["totalWatched"], 0)
        self.assertIsNone(payload["averageRating"])
        self.assertEqual(payload["topGenres"], [])
        self.assertEqual(payload["watchedByYear"], [])
        self.assertEqual(payload["totalReviews"], 0)
        self.assertEqual(payload["totalRatings"], 0)
        self.assertFalse(payload["hasMovieHistory"])

    def test_statistics_for_user_without_ratings(self):
        with self.app.app_context():
            db.session.add(
                Review(
                    user_id=self.owner_id,
                    filme_id="tt7286456",
                    filme_titulo="Joker",
                    generos="Drama",
                    conteudo="Ainda sem nota.",
                    nota=0,
                    created_at=datetime(2026, 2, 3, 12, 0, 0),
                )
            )
            db.session.commit()

        response = self.app.test_client().get(f"/api/users/{self.owner_id}/statistics")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["totalWatched"], 1)
        self.assertIsNone(payload["averageRating"])
        self.assertEqual(payload["totalRatings"], 0)
        self.assertEqual(payload["topGenres"], [{"genre": "Drama", "count": 1}])
        self.assertEqual(payload["watchedByYear"], [{"year": 2026, "count": 1}])

    def test_statistics_handles_incomplete_movie_metadata(self):
        with self.app.app_context():
            db.session.add(
                Review(
                    user_id=self.owner_id,
                    filme_titulo="Filme sem metadados",
                    generos=None,
                    conteudo="Sem genero conhecido.",
                    nota=3,
                    created_at=datetime(2024, 3, 1, 12, 0, 0),
                )
            )
            db.session.commit()

        with patch("service.user_statistics_service.resolver_metadados_filme", side_effect=RuntimeError("sem api")):
            response = self.app.test_client().get(f"/api/users/{self.owner_id}/statistics")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["totalWatched"], 1)
        self.assertEqual(payload["averageRating"], 3.0)
        self.assertEqual(payload["topGenres"], [])
        self.assertEqual(payload["watchedByYear"], [{"year": 2024, "count": 1}])

    def test_statistics_for_missing_user_returns_404(self):
        response = self.app.test_client().get("/api/users/999999/statistics")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["erro"], "Usuario nao encontrado")


if __name__ == "__main__":
    unittest.main()
