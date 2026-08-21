import os
import unittest

# Evita qualquer dependencia do MySQL local quando o modulo app cria sua instancia padrao.
os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash

from app import app as default_app, create_app
from extensions import db
from models.notification import Notification
from models.review import Review
from models.review_comment import ReviewComment
from models.review_like import ReviewLike
from models.user import User


class ReviewInteractionsTestCase(unittest.TestCase):
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
        self.owner_email = "autora@example.com"
        self.actor_email = "leitor@example.com"
        self.other_user_email = "terceiro@example.com"

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            self.owner_id = self._create_user("Autora", self.owner_email)
            self.actor_id = self._create_user("Leitor", self.actor_email)
            self.other_user_id = self._create_user("Terceiro", self.other_user_email)
            review = Review(
                user_id=self.owner_id,
                filme_id="tt0816692",
                filme_titulo="Interestelar",
                conteudo="Uma resenha sobre tempo, família e espaço.",
                nota=5,
            )
            db.session.add(review)
            db.session.commit()
            self.review_id = review.id

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

    def test_like_unlike_duplicate_and_notification(self):
        actor_client = self._logged_client(self.actor_email)

        response = actor_client.post(f"/api/reviews/{self.review_id}/likes")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["likedByCurrentUser"])
        self.assertEqual(response.get_json()["likeCount"], 1)
        with self.app.app_context():
            self.assertEqual(ReviewLike.query.count(), 1)

        duplicate_response = actor_client.post(f"/api/reviews/{self.review_id}/likes")
        self.assertEqual(duplicate_response.status_code, 409)
        with self.app.app_context():
            self.assertEqual(ReviewLike.query.count(), 1)
            notification = Notification.query.one()
            self.assertEqual(notification.type, "like")
            self.assertEqual(notification.recipient_user_id, self.owner_id)
            self.assertEqual(notification.actor_user_id, self.actor_id)
            self.assertFalse(notification.is_read)

        remove_response = actor_client.delete(f"/api/reviews/{self.review_id}/likes")
        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(remove_response.get_json()["likedByCurrentUser"])
        self.assertEqual(remove_response.get_json()["likeCount"], 0)
        with self.app.app_context():
            self.assertEqual(ReviewLike.query.count(), 0)

    def test_self_like_does_not_notify_author(self):
        owner_client = self._logged_client(self.owner_email)

        response = owner_client.post(f"/api/reviews/{self.review_id}/likes")
        self.assertEqual(response.status_code, 201)
        with self.app.app_context():
            self.assertEqual(Notification.query.count(), 0)

    def test_comment_validation_association_and_notification(self):
        actor_client = self._logged_client(self.actor_email)

        empty_response = actor_client.post(
            f"/api/reviews/{self.review_id}/comments",
            json={"content": "   "},
        )
        self.assertEqual(empty_response.status_code, 400)
        with self.app.app_context():
            self.assertEqual(ReviewComment.query.count(), 0)

        response = actor_client.post(
            f"/api/reviews/{self.review_id}/comments",
            json={"content": "Também adorei a construção da personagem principal."},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        with self.app.app_context():
            comment = db.session.get(ReviewComment, payload["id"])
            self.assertEqual(comment.user_id, self.actor_id)
            self.assertEqual(comment.review_id, self.review_id)
            self.assertEqual(comment.conteudo, "Também adorei a construção da personagem principal.")
            notification = Notification.query.one()
            self.assertEqual(notification.type, "comment")
            self.assertEqual(notification.comment_id, comment.id)
            self.assertEqual(notification.recipient_user_id, self.owner_id)

        comments_response = self.app.test_client().get(f"/api/reviews/{self.review_id}/comments")
        self.assertEqual(comments_response.status_code, 200)
        self.assertEqual(comments_response.get_json()["commentCount"], 1)

    def test_self_comment_does_not_create_notification(self):
        owner_client = self._logged_client(self.owner_email)

        response = owner_client.post(
            f"/api/reviews/{self.review_id}/comments",
            json={"content": "Complementando a minha própria resenha."},
        )
        self.assertEqual(response.status_code, 201)
        with self.app.app_context():
            self.assertEqual(ReviewComment.query.count(), 1)
            self.assertEqual(Notification.query.count(), 0)

    def test_notifications_are_scoped_readable_and_redirect_to_review(self):
        actor_client = self._logged_client(self.actor_email)
        comment_response = actor_client.post(
            f"/api/reviews/{self.review_id}/comments",
            json={"content": "Quero rever esse filme depois da sua análise."},
        )
        self.assertEqual(comment_response.status_code, 201)
        comment_id = comment_response.get_json()["id"]

        owner_client = self._logged_client(self.owner_email)
        notifications_response = owner_client.get("/api/notifications")
        self.assertEqual(notifications_response.status_code, 200)
        notifications_payload = notifications_response.get_json()
        self.assertEqual(notifications_payload["unreadCount"], 1)
        notification = notifications_payload["notifications"][0]
        self.assertEqual(notification["commentId"], comment_id)
        self.assertIn(f"/reviews/{self.review_id}", notification["targetUrl"])

        other_client = self._logged_client(self.other_user_email)
        denied_response = other_client.post(f"/api/notifications/{notification['id']}/read")
        self.assertEqual(denied_response.status_code, 404)

        read_response = owner_client.post(f"/api/notifications/{notification['id']}/read")
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(owner_client.get("/api/notifications").get_json()["unreadCount"], 0)

        redirect_response = owner_client.get(notification["targetUrl"])
        self.assertEqual(redirect_response.status_code, 302)
        self.assertIn(f"/users/{self.owner_id}?review={self.review_id}&comment={comment_id}", redirect_response.location)
        self.assertTrue(redirect_response.location.endswith(f"#review-{self.review_id}"))

        public_review_page = owner_client.get(
            f"/users/{self.owner_id}?review={self.review_id}&comment={comment_id}"
        )
        self.assertEqual(public_review_page.status_code, 200)
        self.assertIn(f'id="review-{self.review_id}"'.encode(), public_review_page.data)

    def test_notification_control_is_rendered_on_authenticated_navigation(self):
        owner_client = self._logged_client(self.owner_email)

        for path in ("/pesquisa", "/catalogo", "/perfil", "/users"):
            response = owner_client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"data-notifications", response.data)


if __name__ == "__main__":
    unittest.main()
