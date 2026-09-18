import os
import unittest

os.environ["DATABASE_URL"] = "sqlite://"

from werkzeug.security import generate_password_hash

from app import app as default_app, create_app
from extensions import db
from models.user import User


class UserFollowTestCase(unittest.TestCase):
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
        self.user_email = "seguidor@example.com"
        self.target_email = "alvo@example.com"
        self.other_email = "outro@example.com"

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.user_id = self._create_user("Seguidor", self.user_email)
            self.target_id = self._create_user("Alvo", self.target_email)
            self.other_id = self._create_user("Outro", self.other_email)

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

    def test_follow_and_unfollow_updates_relationships_and_counts(self):
        client = self._logged_client(self.user_email)

        follow_response = client.post(f"/api/users/{self.target_id}/follow")
        self.assertEqual(follow_response.status_code, 201)
        payload = follow_response.get_json()
        self.assertTrue(payload["isFollowing"])
        self.assertEqual(payload["followingCount"], 1)
        self.assertEqual(payload["followerCount"], 1)

        followers_response = self.app.test_client().get(f"/api/users/{self.target_id}/followers")
        self.assertEqual(followers_response.status_code, 200)
        self.assertEqual(len(followers_response.get_json()["users"]), 1)
        self.assertEqual(followers_response.get_json()["users"][0]["id"], self.user_id)

        following_response = client.get(f"/api/users/{self.user_id}/following")
        self.assertEqual(following_response.status_code, 200)
        self.assertEqual(len(following_response.get_json()["users"]), 1)
        self.assertEqual(following_response.get_json()["users"][0]["id"], self.target_id)

        unfollow_response = client.delete(f"/api/users/{self.target_id}/follow")
        self.assertEqual(unfollow_response.status_code, 200)
        self.assertFalse(unfollow_response.get_json()["isFollowing"])
        self.assertEqual(unfollow_response.get_json()["followingCount"], 0)
        self.assertEqual(unfollow_response.get_json()["followerCount"], 0)

    def test_follow_rules_enforce_auth_and_self_protection(self):
        anonymous_response = self.app.test_client().post(f"/api/users/{self.target_id}/follow")
        self.assertEqual(anonymous_response.status_code, 401)

        client = self._logged_client(self.user_email)
        self_follow_response = client.post(f"/api/users/{self.user_id}/follow")
        self.assertEqual(self_follow_response.status_code, 400)

        client.post(f"/api/users/{self.target_id}/follow")
        duplicate_response = client.post(f"/api/users/{self.target_id}/follow")
        self.assertEqual(duplicate_response.status_code, 409)

    def test_follow_modal_payload_contains_user_information(self):
        client = self._logged_client(self.user_email)
        client.post(f"/api/users/{self.target_id}/follow")

        response = client.get(f"/api/users/{self.user_id}/following")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["users"][0]["username"], "Alvo")
        self.assertIn("displayName", payload["users"][0])

    def test_profile_page_renders_follow_button_state(self):
        client = self._logged_client(self.user_email)
        client.post(f"/api/users/{self.target_id}/follow")

        profile_response = client.get(f"/users/{self.target_id}")
        self.assertEqual(profile_response.status_code, 200)
        self.assertIn(b"Seguindo", profile_response.data)


if __name__ == "__main__":
    unittest.main()
