from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.test import TestCase
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------- #
#               User registration and token generation endpoints               #
# ---------------------------------------------------------------------------- #


class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="Password123!"
        )
        self.token = Token.objects.create(user=self.user)
        self.token.save()

    def test_register_user(self):
        # when
        response = self.client.post(
            "/api/users/",
            {
                "username": "test_user2",
                "email": "test_user2@example.com",
                "password": "Password123!",
            },
        )

        # then
        self.assertEqual(response.status_code, 201)

    def test_get_current_user(self):
        # given
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))

        # when
        response = self.client.get("/api/users/me/")

        # then
        self.assertEqual(
            response.data,
            {"email": "test_user@example.com", "id": 1, "username": "test_user"},
        )

    def test_obtain_token(self):
        # when
        response = self.client.post(
            "/token/login",
            {
                "username": "test_user",
                "email": "test_user@example.com",
                "password": "Password123!",
            },
        )

        # then
        self.assertEqual(response.data["token"], str(self.token))
