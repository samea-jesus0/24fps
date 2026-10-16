import os
import unittest
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash

from app import app as default_app, create_app
from extensions import db
from models.review import Review
from models.user import User
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie
from service.recommendation_service import (
    _load_candidates,
    _score_candidate,
    get_movie_recommendations,
)
from service.filme_service import CATALOG_SECTIONS


class RecommendationsTestCase(unittest.TestCase):
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
                "RECOMMENDATION_WEIGHTS": {
                    "reviews": 0.60,
                    "wishlist": 0.25,
                    "popularity": 0.15,
                },
            }
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.user_id = self._create_user("Cinefilo", "cinefilo@example.com")
            self.other_user_id = self._create_user("Outra", "outra@example.com")
            db.session.add_all(
                [
                    Review(
                        user_id=self.user_id,
                        filme_id="tt-reviewed",
                        filme_titulo="Filme avaliado",
                        generos="Drama",
                        conteudo="Gostei muito.",
                        nota=5,
                    ),
                    Review(
                        user_id=self.user_id,
                        filme_id="tt-disliked",
                        filme_titulo="Filme mal avaliado",
                        generos="Action",
                        conteudo="Nao gostei.",
                        nota=1,
                    ),
                    Review(
                        user_id=self.other_user_id,
                        filme_id="tt-other",
                        filme_titulo="Filme de outra pessoa",
                        generos="Animation",
                        conteudo="Outra resenha.",
                        nota=5,
                    ),
                ]
            )
            wishlist = Wishlist(
                user_id=self.user_id,
                titulo="Quero ver",
                is_public=False,
            )
            db.session.add(wishlist)
            db.session.flush()
            db.session.add(
                WishlistMovie(
                    wishlist_id=wishlist.id,
                    movie_key="imdb:tt-wishlisted",
                    filme_id="tt-wishlisted",
                    filme_titulo="Filme na wishlist",
                )
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
        return user.id

    def _logged_client(self):
        client = self.app.test_client()
        response = client.post(
            "/login",
            data={"email": "cinefilo@example.com", "senha": "senha-segura"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        return client

    def test_review_ratings_increase_and_decrease_genre_affinity(self):
        weights = {"reviews": 0.60, "wishlist": 0.25, "popularity": 0.15}
        liked, _ = _score_candidate(
            {"generos": ["Drama"], "imdb_valor": 6},
            {"drama": 1.0, "action": -1.0},
            set(),
            weights,
        )
        disliked, _ = _score_candidate(
            {"generos": ["Action"], "imdb_valor": 6},
            {"drama": 1.0, "action": -1.0},
            set(),
            weights,
        )
        self.assertGreater(liked, disliked)

    def test_recommendations_are_personalized_and_exclude_existing_movies(self):
        candidates = [
            {
                "id": "tt-reviewed",
                "titulo": "Filme avaliado",
                "generos": ["Drama"],
                "imdb_valor": 9.8,
            },
            {
                "id": "tt-reviewed-title-match",
                "titulo": "Filme avaliado",
                "generos": ["Drama"],
                "imdb_valor": 9.9,
            },
            {
                "id": "tt-wishlisted",
                "titulo": "Filme na wishlist",
                "generos": ["Sci-Fi"],
                "imdb_valor": 9.7,
            },
            {
                "id": "tt-wishlisted-title-match",
                "titulo": "Filme na wishlist",
                "generos": ["Sci-Fi"],
                "imdb_valor": 9.9,
            },
            {
                "id": "tt-other",
                "titulo": "Filme de outra pessoa",
                "generos": ["Animation"],
                "imdb_valor": 9.6,
            },
            {
                "id": "tt-drama",
                "titulo": "Outro drama",
                "generos": ["Drama"],
                "imdb_valor": 7.0,
                "sinopse": "Uma historia de teste.",
            },
            {
                "id": "tt-action",
                "titulo": "Acao rejeitada",
                "generos": ["Action"],
                "imdb_valor": 10.0,
            },
            {
                "id": "tt-sci-fi",
                "titulo": "Ficcao para wishlist",
                "generos": ["Sci-Fi"],
                "imdb_valor": 6.0,
            },
        ]
        with self.app.app_context(), patch(
            "service.recommendation_service._resolve_wishlist_genres",
            return_value={"sci-fi"},
        ), patch(
            "service.recommendation_service._load_candidates",
            return_value=candidates,
        ):
            recommendations = get_movie_recommendations(self.user_id)

        ids = [movie["id"] for movie in recommendations]
        self.assertNotIn("tt-reviewed", ids)
        self.assertNotIn("tt-reviewed-title-match", ids)
        self.assertNotIn("tt-wishlisted", ids)
        self.assertNotIn("tt-wishlisted-title-match", ids)
        self.assertIn("tt-other", ids)
        self.assertIn("tt-drama", ids)
        self.assertIn("tt-sci-fi", ids)
        self.assertNotIn("tt-action", ids[:1])
        self.assertEqual(len(ids), len(set(ids)))
        drama = next(movie for movie in recommendations if movie["id"] == "tt-drama")
        self.assertEqual(drama["reason"], "Porque você gosta de Drama")
        self.assertEqual(drama["synopsis"], "Uma historia de teste.")
        sci_fi = next(movie for movie in recommendations if movie["id"] == "tt-sci-fi")
        self.assertEqual(sci_fi["reason"], "Porque Sci-Fi está na sua wishlist")

    def test_candidate_pool_keeps_candidates_from_each_interested_genre(self):
        expected_ids = [
            *CATALOG_SECTIONS[0]["featured_ids"],
            *CATALOG_SECTIONS[1]["featured_ids"],
        ]
        with self.app.app_context(), patch(
            "service.recommendation_service.buscar_ids_filmes_por_termo",
            return_value=[],
        ), patch(
            "service.recommendation_service.buscar_filme_por_id",
            side_effect=lambda movie_id: {
                "id": movie_id,
                "titulo": movie_id,
                "generos": [],
            },
        ):
            candidates = _load_candidates(
                [
                    CATALOG_SECTIONS[0]["genre_name"].lower(),
                    CATALOG_SECTIONS[1]["genre_name"].lower(),
                ]
            )

        self.assertEqual({movie["id"] for movie in candidates}, set(expected_ids))

    def test_candidate_pool_uses_multiple_search_terms_for_more_choices(self):
        section = CATALOG_SECTIONS[0]
        featured_ids = section["featured_ids"]
        search_calls = []

        def search_ids(term, limit):
            search_calls.append(term)
            return [f"tt-search-{len(search_calls)}-{index}" for index in range(limit)]

        with self.app.app_context(), patch(
            "service.recommendation_service.buscar_ids_filmes_por_termo",
            side_effect=search_ids,
        ), patch(
            "service.recommendation_service.buscar_filme_por_id",
            side_effect=lambda movie_id: {
                "id": movie_id,
                "titulo": movie_id,
                "generos": [section["genre_name"]],
            },
        ):
            candidates = _load_candidates([section["genre_name"].lower()])

        self.assertEqual(len(candidates), 18)
        self.assertGreaterEqual(len(search_calls), 2)
        self.assertTrue(set(featured_ids).issubset({movie["id"] for movie in candidates}))

    def test_rotation_changes_page_within_the_top_relevant_candidates(self):
        candidates = [
            {
                "id": f"tt-{index}",
                "titulo": f"Filme {index:02}",
                "generos": ["Drama"],
                "imdb": str(10 - index / 10),
                "imdb_valor": 10 - index / 10,
            }
            for index in range(14)
        ]
        with self.app.app_context(), patch(
            "service.recommendation_service._resolve_wishlist_genres",
            return_value=set(),
        ), patch(
            "service.recommendation_service._load_candidates",
            return_value=candidates,
        ):
            first = get_movie_recommendations(self.user_id, limit=5, rotation=0)
            next_page = get_movie_recommendations(self.user_id, limit=5, rotation=1)

        first_ids = {movie["id"] for movie in first}
        next_ids = {movie["id"] for movie in next_page}
        self.assertEqual(len(first), 5)
        self.assertEqual(len(next_page), 5)
        self.assertNotEqual(first_ids, next_ids)
        self.assertEqual(first[0]["id"], "tt-0")
        self.assertTrue(next_ids.issubset({movie["id"] for movie in candidates[:10]}))

    def test_endpoint_passes_rotation_to_recommendation_service(self):
        client = self._logged_client()
        candidates = [
            {
                "id": f"tt-api-{index}",
                "titulo": f"Filme {index:02}",
                "generos": ["Drama"],
                "imdb": str(10 - index / 10),
                "imdb_valor": 10 - index / 10,
            }
            for index in range(14)
        ]
        with patch(
            "service.recommendation_service._resolve_wishlist_genres",
            return_value=set(),
        ), patch(
            "service.recommendation_service._load_candidates",
            return_value=candidates,
        ):
            first = client.get("/api/recommendations?rotation=0").get_json()
            next_page = client.get("/api/recommendations?rotation=1").get_json()

        first_ids = {movie["id"] for movie in first["recommendations"]}
        next_ids = {movie["id"] for movie in next_page["recommendations"]}
        self.assertNotEqual(first_ids, next_ids)

    def test_authenticated_endpoint_and_anonymous_access(self):
        anonymous = self.app.test_client().get("/api/recommendations")
        self.assertEqual(anonymous.status_code, 302)

        client = self._logged_client()
        page = client.get("/pesquisa")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Recomendados para você".encode(), page.data)

        with patch(
            "service.recommendation_service._resolve_wishlist_genres",
            return_value=set(),
        ), patch(
            "service.recommendation_service._load_candidates",
            return_value=[
                {
                    "id": "tt-example",
                    "titulo": "Filme exemplo",
                    "generos": ["Drama"],
                    "imdb": "8.0",
                    "imdb_valor": 8.0,
                }
            ],
        ):
            response = client.get("/api/recommendations")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["recommendations"][0]["title"], "Filme exemplo")

    def test_new_user_gets_popularity_ordered_candidates(self):
        with self.app.app_context():
            new_user_id = self._create_user("Novo", "novo@example.com")
            with patch(
                "service.recommendation_service._load_candidates",
                return_value=[
                    {"id": "tt-low", "titulo": "Nota menor", "generos": ["Drama"], "imdb_valor": 6},
                    {"id": "tt-high", "titulo": "Nota maior", "generos": ["Drama"], "imdb_valor": 9},
                ],
            ):
                recommendations = get_movie_recommendations(new_user_id)

        self.assertEqual(recommendations[0]["id"], "tt-high")


if __name__ == "__main__":
    unittest.main()
