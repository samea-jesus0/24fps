import os
import unittest
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash
from sqlalchemy import event

from app import app as default_app, create_app
from extensions import db
from models.review import Review
from models.user import User
from models.user_follow import UserFollow
from models.wishlist import Wishlist
from models.wishlist_movie import WishlistMovie
from service.match_service import get_match_details
from service.match_service import get_user_matches


class MatchesTestCase(unittest.TestCase):
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
            self.current_id = self._create_user("Felipe", "felipe@example.com")
            self.other_id = self._create_user("Maria", "maria@example.com")
            self.empty_id = self._create_user("Sem histórico", "empty@example.com")

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

    def _add_review(self, user_id, title, movie_id=None, genres=None, rating=0, offset=0):
        review = Review(
            user_id=user_id,
            filme_id=movie_id,
            filme_titulo=title,
            generos=genres,
            conteudo="Resenha de teste.",
            nota=rating,
            created_at=datetime(2025, 1, 1) + timedelta(seconds=offset),
            updated_at=datetime(2025, 1, 1) + timedelta(seconds=offset),
        )
        db.session.add(review)
        db.session.commit()
        return review.id

    def _seed_shared_movies(self, count=1, current_rating=5, other_rating=5, genre="Drama"):
        for index in range(count):
            movie_id = f"tt-shared-{index}"
            title = f"Filme compartilhado {index}"
            self._add_review(self.current_id, title, movie_id, genre, current_rating, index)
            self._add_review(self.other_id, title, movie_id, genre, other_rating, index)

    def _details(self, other_id=None):
        with self.app.test_request_context():
            return get_match_details(self.current_id, other_id or self.other_id)

    def _logged_client(self):
        client = self.app.test_client()
        response = client.post(
            "/login",
            data={"email": "felipe@example.com", "senha": "senha-segura"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        return client

    def test_identical_ratings_produce_full_raw_similarity_but_one_title_is_not_a_100_match(self):
        with self.app.app_context():
            self._seed_shared_movies(count=1)
            details = self._details()

        self.assertEqual(details["components"]["ratingsRaw"], 100)
        self.assertEqual(details["components"]["ratings"], 60)
        self.assertLess(details["compatibility"], 100)
        self.assertEqual(details["confidence"], "low")

    def test_different_ratings_follow_the_twenty_point_scale(self):
        with self.app.app_context():
            for difference in range(1, 5):
                self._add_review(self.current_id, f"Current {difference}", f"tt-current-{difference}", "Drama", 5, difference)
                self._add_review(self.other_id, f"Other {difference}", f"tt-current-{difference}", "Drama", 5 - difference, difference)
            details = self._details()

        # Differences 1 through 4 map to 80, 60, 40 and 20 percent. A
        # difference of five would require a zero rating, which means "unrated" here.
        self.assertEqual(details["components"]["ratingsRaw"], 50)
        self.assertEqual(details["commonRatedMoviesCount"], 4)

    def test_genre_similarity_is_high_for_identical_genre_frequencies(self):
        with self.app.app_context():
            for index, genre in enumerate(["Sci-Fi", "Sci-Fi", "Drama"]):
                self._add_review(self.current_id, f"A {index}", f"tt-a-{index}", genre, 4, index)
                self._add_review(self.other_id, f"B {index}", f"tt-b-{index}", genre, 4, index)
            details = self._details()

        self.assertEqual(details["components"]["genres"], 100)
        self.assertEqual(details["commonGenres"], ["Sci-Fi", "Drama"])

    def test_partially_shared_genres_have_a_partial_similarity(self):
        with self.app.app_context():
            for index, genre in enumerate(["Sci-Fi", "Drama", "Action"]):
                self._add_review(self.current_id, f"A {index}", f"tt-a-{index}", genre, 4, index)
            for index, genre in enumerate(["Sci-Fi", "Drama", "Comedy"]):
                self._add_review(self.other_id, f"B {index}", f"tt-b-{index}", genre, 4, index)
            details = self._details()

        self.assertGreater(details["components"]["genres"], 0)
        self.assertLess(details["components"]["genres"], 100)
        self.assertEqual(details["commonGenres"], ["Drama", "Sci-Fi"])

    def test_no_shared_genres_returns_zero_genre_similarity(self):
        with self.app.app_context():
            self._add_review(self.current_id, "A", "tt-a", "Drama", 4)
            self._add_review(self.other_id, "B", "tt-b", "Action", 4)
            details = self._details()

        self.assertEqual(details["components"]["genres"], 0)
        self.assertEqual(details["commonGenres"], [])

    def test_common_movies_are_returned_and_counted(self):
        with self.app.app_context():
            self._seed_shared_movies(count=2)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 2)
        self.assertEqual(len(details["commonMovies"]), 2)
        self.assertEqual(details["commonMovies"][0]["currentUserRating"], 5)

    def test_no_common_movies_is_a_supported_zero_similarity_case(self):
        with self.app.app_context():
            self._add_review(self.current_id, "Dune", "tt-dune", "Sci-Fi", 5)
            self._add_review(self.other_id, "Parasite", "tt-parasite", "Drama", 5)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 0)
        self.assertEqual(details["commonRatedMoviesCount"], 0)
        self.assertEqual(details["components"]["ratings"], None)
        self.assertEqual(details["components"]["movies"], 0)

    def test_rating_zero_is_not_compared_but_its_review_is_watched_history(self):
        with self.app.app_context():
            self._seed_shared_movies(count=1, current_rating=0, other_rating=5)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 1)
        self.assertEqual(details["commonRatedMoviesCount"], 0)
        self.assertIsNone(details["components"]["ratingsRaw"])
        self.assertIsNone(details["commonMovies"][0]["currentUserRating"])

    def test_user_without_reviews_gets_empty_match_list(self):
        client = self.app.test_client()
        client.post("/login", data={"email": "empty@example.com", "senha": "senha-segura"})

        response = client.get("/api/matches")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["matches"], [])

    def test_existing_user_without_history_has_a_safe_empty_detail(self):
        with self.app.app_context():
            details = self._details(self.empty_id)

        self.assertFalse(details["hasComparisonData"])
        self.assertEqual(details["compatibility"], 0)
        self.assertEqual(details["confidence"], "low")
        self.assertIn("histórico", details["message"])

    def test_missing_user_returns_404(self):
        client = self._logged_client()

        response = client.get("/api/matches/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["erro"], "Usuário não encontrado.")

    def test_matches_page_and_api_require_authentication(self):
        anonymous = self.app.test_client()

        page_response = anonymous.get("/matches")
        list_response = anonymous.get("/api/matches")
        detail_response = anonymous.get(f"/api/matches/{self.other_id}")

        self.assertEqual(page_response.status_code, 302)
        self.assertEqual(list_response.status_code, 401)
        self.assertEqual(detail_response.status_code, 401)

    def test_current_user_is_not_returned_as_a_match_and_self_detail_is_rejected(self):
        with self.app.app_context():
            self._seed_shared_movies()
        client = self._logged_client()

        list_response = client.get("/api/matches")
        self_response = client.get(f"/api/matches/{self.current_id}")

        self.assertEqual(list_response.status_code, 200)
        self.assertNotIn(self.current_id, [match["userId"] for match in list_response.get_json()["matches"]])
        self.assertEqual(self_response.status_code, 400)

    def test_matches_are_ordered_from_highest_compatibility_to_lowest(self):
        with self.app.app_context():
            low_id = self._create_user("João", "joao@example.com")
            for index in range(5):
                self._add_review(self.current_id, f"Filme {index}", f"tt-order-{index}", "Drama", 5, index)
                self._add_review(self.other_id, f"Filme {index}", f"tt-order-{index}", "Drama", 5, index)
                self._add_review(low_id, f"Filme {index}", f"tt-order-{index}", "Action", 1, index)
        payload = self._logged_client().get("/api/matches").get_json()["matches"]

        self.assertEqual(payload[0]["userId"], self.other_id)
        self.assertEqual(payload[1]["userId"], low_id)
        self.assertGreaterEqual(payload[0]["compatibility"], payload[1]["compatibility"])

    def test_unfollowed_users_are_discoverable_and_empty_profiles_are_skipped(self):
        with self.app.app_context():
            self._seed_shared_movies(count=1)
        payload = self._logged_client().get("/api/matches").get_json()["matches"]

        self.assertEqual([match["userId"] for match in payload], [self.other_id])
        self.assertFalse(payload[0]["isFollowing"])

    def test_matches_and_detail_pages_render_and_reuse_the_follow_control(self):
        with self.app.app_context():
            self._seed_shared_movies(count=5)
            db.session.add(UserFollow(follower_user_id=self.current_id, followed_user_id=self.other_id))
            db.session.commit()
        client = self._logged_client()

        page = client.get("/matches")
        detail = client.get(f"/matches/{self.other_id}")

        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Matches cinematogr", page.data)
        self.assertIn(b"data-follow-toggle", page.data)
        self.assertIn(b"Seguindo", page.data)
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Filmes em comum", detail.data)
        self.assertIn(b"Dram", detail.data)

    def test_match_listing_uses_a_fixed_number_of_batched_queries(self):
        with self.app.app_context():
            self._seed_shared_movies(count=1)
            for index in range(5):
                user_id = self._create_user(f"Pessoa {index}", f"pessoa-{index}@example.com")
                self._add_review(user_id, f"Filme {index}", f"tt-extra-{index}", "Drama", 4, index)

            statements = []

            def record_statement(_connection, _cursor, statement, _parameters, _context, _executemany):
                statements.append(statement)

            with self.app.test_request_context():
                event.listen(db.engine, "before_cursor_execute", record_statement)
                try:
                    matches = get_user_matches(self.current_id)
                finally:
                    event.remove(db.engine, "before_cursor_execute", record_statement)

        self.assertEqual(len(matches), 6)
        self.assertEqual(len(statements), 3)

    def test_private_wishlists_do_not_affect_match_data(self):
        with self.app.app_context():
            self._add_review(self.current_id, "Dune", "tt-dune", "Sci-Fi", 5)
            self._add_review(self.other_id, "Arrival", "tt-arrival", "Drama", 4)
            private_list = Wishlist(user_id=self.current_id, titulo="Minha lista privada", is_public=False)
            db.session.add(private_list)
            db.session.flush()
            db.session.add(
                WishlistMovie(
                    wishlist_id=private_list.id,
                    movie_key="imdb:tt-arrival",
                    filme_id="tt-arrival",
                    filme_titulo="Arrival",
                )
            )
            db.session.commit()
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 0)
        self.assertEqual(details["components"]["movies"], 0)

    def test_genre_names_are_case_and_whitespace_insensitive(self):
        with self.app.app_context():
            self._add_review(self.current_id, "Filme A", "tt-a", "Action, SCI-FI", 4)
            self._add_review(self.other_id, "Filme B", "tt-b", " action , sci-fi ", 4)
            details = self._details()

        self.assertEqual(details["components"]["genres"], 100)
        self.assertEqual(details["commonGenres"], ["Action", "SCI-FI"])

    def test_duplicate_reviews_of_same_movie_are_counted_once(self):
        with self.app.app_context():
            self._add_review(self.current_id, "Dune", " TT-001 ", "Sci-Fi", 4, 1)
            self._add_review(self.current_id, "Dune (duplicate)", "tt-001", "", 5, 2)
            self._add_review(self.other_id, "Dune", "tt-001", "Sci-Fi", 5, 1)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 1)
        self.assertEqual(details["commonRatedMoviesCount"], 1)
        self.assertEqual(len(details["commonMovies"]), 1)
        self.assertEqual(details["commonMovies"][0]["currentUserRating"], 5)

    def test_confidence_thresholds_are_based_on_unique_shared_movies(self):
        with self.app.app_context():
            self._seed_shared_movies(count=2)
            low = self._details()["confidence"]
            self._seed_shared_movies(count=6, current_rating=4, other_rating=4)
            medium = self._details()["confidence"]
            self._seed_shared_movies(count=15, current_rating=3, other_rating=3)
            high = self._details()["confidence"]

        self.assertEqual((low, medium, high), ("low", "medium", "high"))

    def test_public_profile_remains_available_without_login_and_hides_match(self):
        with self.app.app_context():
            self._seed_shared_movies()

        response = self.app.test_client().get(f"/users/{self.other_id}")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"ver detalhes do match", response.data.lower())

    def test_authenticated_public_profile_shows_compatibility(self):
        with self.app.app_context():
            self._seed_shared_movies(count=5)
        response = self._logged_client().get(f"/users/{self.other_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Compatibilidade".encode(), response.data)
        self.assertIn(b"ver detalhes do match", response.data.lower())

    def test_profiles_with_missing_genre_metadata_still_return_a_match(self):
        with self.app.app_context():
            self._add_review(self.current_id, "Sem metadados", None, None, 3)
            self._add_review(self.other_id, "Sem metadados", None, None, 4)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 1)
        self.assertEqual(details["commonGenres"], [])
        self.assertEqual(details["compatibility"], 62)

    def test_movie_titles_are_normalised_when_ids_are_missing(self):
        with self.app.app_context():
            self._add_review(self.current_id, "  The   Matrix ", None, "Sci-Fi", 5)
            self._add_review(self.other_id, "the matrix", None, "Sci-Fi", 5)
            details = self._details()

        self.assertEqual(details["commonMoviesCount"], 1)
        self.assertEqual(details["commonMovies"][0]["movieId"], None)


if __name__ == "__main__":
    unittest.main()
