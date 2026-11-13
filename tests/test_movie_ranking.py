import os
import unittest
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"

from app import app as default_app, create_app
from extensions import db
from models.review import Review
from models.user import User
from service.movie_ranking_service import get_movie_ranking


class MovieRankingTestCase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with default_app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.user_ids = [self._create_user(index) for index in range(12)]
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    @staticmethod
    def _create_user(index):
        user = User(
            nome=f"Avaliador {index}",
            display_name=f"Avaliador {index}",
            email=f"avaliador{index}@example.com",
            senha="hash-de-teste",
        )
        db.session.add(user)
        db.session.flush()
        return user.id

    def _add_movie(
        self,
        title,
        ratings,
        movie_id=None,
        users=None,
        poster="https://example.com/poster.jpg",
        year=2024,
        genres="Drama, Sci-Fi",
    ):
        with self.app.app_context():
            users = users or self.user_ids[: len(ratings)]
            reviews = [
                Review(
                    user_id=users[index],
                    filme_id=movie_id,
                    filme_titulo=title,
                    poster_url=poster,
                    generos=genres,
                    ano_lancamento=year,
                    conteudo=f"Texto privado de avaliação {index}",
                    nota=rating,
                )
                for index, rating in enumerate(ratings)
            ]
            db.session.add_all(reviews)
            db.session.commit()
            return reviews

    def test_movie_with_highest_average_is_first(self):
        self._add_movie("Nota menor", [4, 4, 4, 4, 4], movie_id="tt-low")
        self._add_movie("Nota maior", [5, 5, 5, 5, 4], movie_id="tt-high")

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(ranking[0]["title"], "Nota maior")
        self.assertEqual(ranking[0]["averageRating"], 4.8)

    def test_only_five_movies_are_returned(self):
        for index in range(6):
            self._add_movie(f"Filme {index}", [5] * 5, movie_id=f"tt-{index}")

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(len(ranking), 5)
        self.assertEqual([movie["position"] for movie in ranking], [1, 2, 3, 4, 5])

    def test_movie_with_fewer_than_five_distinct_raters_is_excluded(self):
        self._add_movie("Poucos avaliadores", [5] * 4, movie_id="tt-four")
        self._add_movie("Elegível", [4] * 5, movie_id="tt-five")

        with self.app.app_context():
            titles = [movie["title"] for movie in get_movie_ranking()]

        self.assertEqual(titles, ["Elegível"])

    def test_repeated_reviews_from_one_user_do_not_meet_minimum_rater_count(self):
        self._add_movie(
            "Vários textos, uma pessoa",
            [5, 5, 5, 5, 5],
            movie_id="tt-one-rater",
            users=[self.user_ids[0]] * 5,
        )

        with self.app.app_context():
            self.assertEqual(get_movie_ranking(), [])

    def test_zero_ratings_do_not_affect_average_or_rating_count(self):
        self._add_movie("Filme válido", [5, 5, 5, 4, 4], movie_id="tt-valid")
        self._add_movie("Sem nota", [0] * 5, movie_id="tt-unrated")
        self._add_movie(
            "Filme válido",
            [0],
            movie_id="tt-valid",
            users=[self.user_ids[5]],
        )

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["ratingCount"], 5)
        self.assertEqual(ranking[0]["averageRating"], 4.6)

    def test_tie_is_broken_by_review_count(self):
        self._add_movie(
            "Mais avaliações",
            [5, 5, 4, 4, 3, 3],
            movie_id="tt-more-reviews",
            users=[self.user_ids[0], self.user_ids[1], self.user_ids[2], self.user_ids[3], self.user_ids[4], self.user_ids[0]],
        )
        self._add_movie("Menos avaliações", [5, 4, 4, 4, 3], movie_id="tt-fewer-reviews")

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(ranking[0]["title"], "Mais avaliações")
        self.assertEqual(ranking[0]["averageRating"], ranking[1]["averageRating"])

    def test_tie_is_then_broken_by_distinct_rater_count(self):
        self._add_movie(
            "Zulu",
            [5, 5, 4, 4, 3, 3],
            movie_id="tt-more-raters",
            users=self.user_ids[:6],
        )
        self._add_movie(
            "Alpha",
            [5, 5, 4, 4, 3, 3],
            movie_id="tt-fewer-raters",
            users=[self.user_ids[0], self.user_ids[1], self.user_ids[2], self.user_ids[3], self.user_ids[4], self.user_ids[0]],
        )

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(ranking[0]["title"], "Zulu")

    def test_full_tie_is_broken_by_title_alphabetically(self):
        self._add_movie("Zulu", [4, 4, 4, 4, 4], movie_id="tt-zulu")
        self._add_movie("Alpha", [4, 4, 4, 4, 4], movie_id="tt-alpha")

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual([movie["title"] for movie in ranking], ["Alpha", "Zulu"])

    def test_equal_external_ids_with_different_titles_are_one_movie(self):
        self._add_movie("Título original", [5, 4], movie_id="TT123 ", users=self.user_ids[:2])
        self._add_movie("Outro título salvo", [4, 3, 4], movie_id="tt123", users=self.user_ids[2:5])

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["ratingCount"], 5)
        self.assertEqual(ranking[0]["averageRating"], 4.0)

    def test_normalized_title_is_used_when_movie_id_is_missing(self):
        titles = ["  Parasita  ", "parasita", "PARASITA", "PaRaSiTa", " parasita "]
        reviews = []
        for index, title in enumerate(titles):
            reviews.extend(self._add_movie(title, [4], users=[self.user_ids[index]]))

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["ratingCount"], 5)
        self.assertEqual(ranking[0]["title"], "parasita")

    def test_each_review_row_is_counted_once_and_missing_metadata_is_safe(self):
        self._add_movie(
            "Sem ficha completa",
            [5, 4, 4, 3, 4],
            movie_id="tt-no-metadata",
            poster=None,
            year=None,
            genres=None,
        )

        with self.app.app_context():
            ranking = get_movie_ranking()

        self.assertEqual(ranking[0]["ratingCount"], 5)
        self.assertIsNone(ranking[0]["poster"])
        self.assertIsNone(ranking[0]["year"])
        self.assertEqual(ranking[0]["genres"], [])

    def test_empty_ranking_returns_an_empty_list(self):
        with self.app.app_context():
            self.assertEqual(get_movie_ranking(), [])

    def test_public_page_and_api_work_without_login_and_api_exposes_aggregates_only(self):
        private_text = "Texto privado de avaliação 0"
        self._add_movie("Filme público", [5] * 5, movie_id="tt-public")
        client = self.app.test_client()

        page = client.get("/ranking")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"TOP 5 DA COMUNIDADE", page.data)
        self.assertIn(b'data-poster-fallback="/static/img/default-poster.svg"', page.data)

        with patch("service.filme_service.buscar_filme_por_id", side_effect=AssertionError("OMDb chamada")), patch(
            "service.filme_service.buscar_filme_por_nome", side_effect=AssertionError("OMDb chamada")
        ):
            response = client.get("/api/ranking")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["minimumRatings"], 5)
        self.assertEqual(payload["totalMovies"], 1)
        self.assertEqual(payload["ranking"][0]["title"], "Filme público")
        serialized = response.get_data(as_text=True)
        self.assertNotIn("avaliador0@example.com", serialized)
        self.assertNotIn("Avaliador 0", serialized)
        self.assertNotIn(private_text, serialized)
        self.assertNotIn("conteudo", serialized)


if __name__ == "__main__":
    unittest.main()
