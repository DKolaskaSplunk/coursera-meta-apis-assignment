from functools import partial

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Category, MenuItem

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


# ---------------------------------------------------------------------------- #
#                             Menu-items endpoints                             #
# ---------------------------------------------------------------------------- #


class MenuItemsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="Password123!"
        )
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))

    def test_get_menu_items(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        MenuItem.objects.bulk_create(
            [
                MenuItem(
                    title="Pasta",
                    price=12.99,
                    featured=False,
                    category=main_course_category,
                ),
                MenuItem(
                    title="Salad",
                    price=7.99,
                    featured=True,
                    category=main_course_category,
                ),
            ]
        )

        # when
        response = self.client.get("/api/menu-items/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Pasta")
        self.assertEqual(response.data[1]["title"], "Salad")

    def test_menu_items_when_customer_or_delivery_crew_forbidden_http_methods(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )

        # when
        body = {
            "title": "Burger",
            "price": 9.99,
            "featured": False,
            "category_id": main_course_category.id,
        }
        response = self.client.post(
            "/api/menu-items/", body, content_type="application/json"
        )

        # then
        self.assertEqual(response.status_code, 403)

    def test_get_item(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )

        # when
        response = self.client.get("/api/menu-items/1")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Pasta")

    def test_create_menu_item_when_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )

        # when
        body = {
            "title": "Burger",
            "price": 9.99,
            "featured": False,
            "category_id": main_course_category.id,
        }
        response = self.client.post(
            "/api/menu-items/", body, content_type="application/json"
        )

        # then
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Burger")

    def test_update_menu_item_when_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )

        # when
        body = {
            "title": "Spaghetti",
            "price": 13.99,
            "featured": True,
            "category_id": main_course_category.id,
        }
        response = self.client.put(
            "/api/menu-items/1", body, content_type="application/json"
        )

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Spaghetti")

    def test_delete_menu_item_when_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )

        # when
        response = self.client.delete("/api/menu-items/1")

        # then
        self.assertEqual(response.status_code, 204)


# ---------------------------------------------------------------------------- #
#                        User group management endpoints                       #
# ---------------------------------------------------------------------------- #


class UserGroupManagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="Password123!"
        )
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))

    def test_endpoint_accessible_only_to_manager(self):
        params = (
            (self.client.get, "/api/groups/manager/users"),
            (self.client.post, "/api/groups/manager/users", {"id": 2}),
            (self.client.delete, "/api/groups/manager/users/2"),
            (self.client.get, "/api/groups/delivery-crew/users"),
            (self.client.post, "/api/groups/delivery-crew/users", {"id": 2}),
            (self.client.delete, "/api/groups/delivery-crew/users/2"),
        )

        for api_client_func, *args in params:
            with self.subTest(api_client_call=args):
                # when
                response = partial(api_client_func, *args)()

                # then
                self.assertEqual(response.status_code, 403)

    def test_get_managers(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        # when
        response = self.client.get("/api/groups/manager/users")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user.id)

    def test_add_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        new_user = User.objects.create_user(
            username="new_user", email="new_user@example.com", password="Password123!"
        )
        new_user.groups.add(manager_group)

        # when
        response = self.client.post("/api/groups/manager/users", {"id": new_user.id})

        # then
        self.assertEqual(response.status_code, 201)
        self.assertIn(new_user, manager_group.user_set.all())

    def test_remove_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        # when
        response = self.client.delete(f"/api/groups/manager/users/{self.user.id}")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.user, manager_group.user_set.all())

    def test_get_delivery_crew(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        delivery_crew_group = Group.objects.create(name="Delivery Crew")
        self.user.groups.add(delivery_crew_group)

        # when
        response = self.client.get("/api/groups/delivery-crew/users")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user.id)

    def test_add_delivery_crew(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        delivery_crew_group = Group.objects.create(name="Delivery Crew")

        new_user = User.objects.create_user(
            username="new_user", email="new_user@example.com", password="Password123!"
        )
        new_user.groups.add(delivery_crew_group)

        # when
        response = self.client.post(
            "/api/groups/delivery-crew/users", {"id": new_user.id}
        )

        # then
        self.assertEqual(response.status_code, 201)
        self.assertIn(new_user, delivery_crew_group.user_set.all())

    def test_remove_delivery_crew(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        delivery_crew_group = Group.objects.create(name="Delivery Crew")
        self.user.groups.add(delivery_crew_group)

        # when
        response = self.client.delete(f"/api/groups/delivery-crew/users/{self.user.id}")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.user, delivery_crew_group.user_set.all())
