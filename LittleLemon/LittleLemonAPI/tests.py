from functools import partial

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Cart, Category, MenuItem, Order, OrderItem

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
            (self.client.get, "/api/groups/manager/users/"),
            (self.client.post, "/api/groups/manager/users/", {"id": 2}),
            (self.client.delete, "/api/groups/manager/users/2"),
            (self.client.get, "/api/groups/delivery-crew/users/"),
            (self.client.post, "/api/groups/delivery-crew/users/", {"id": 2}),
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
        response = self.client.get("/api/groups/manager/users/")

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
        response = self.client.post("/api/groups/manager/users/", {"id": new_user.id})

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
        response = self.client.get("/api/groups/delivery-crew/users/")

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
            "/api/groups/delivery-crew/users/", {"id": new_user.id}
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


# ---------------------------------------------------------------------------- #
#                           Cart management endpoints                          #
# ---------------------------------------------------------------------------- #


class CartManagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="Password123!"
        )
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))

    def test_get_empty_cart(self):
        # when
        response = self.client.get("/api/cart/menu-items/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_get_cart_with_items(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        Cart.objects.create(user=self.user, menuitem=menu_item1, quantity=2)

        # when
        response = self.client.get("/api/cart/menu-items/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_add_item_to_cart(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )

        # when
        response = self.client.post(
            "/api/cart/menu-items/",
            {"menuitem_id": menu_item1.id, "quantity": 3},
            content_type="application/json",
        )

        # then
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["quantity"], 3)

    def test_remove_item_from_cart(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        Cart.objects.create(user=self.user, menuitem=menu_item1, quantity=2)

        # when
        response = self.client.delete("/api/cart/menu-items/")

        # then
        self.assertEqual(response.status_code, 204)


# ---------------------------------------------------------------------------- #
#                          Order management endpoints                          #
# ---------------------------------------------------------------------------- #


class OrderManagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="Password123!"
        )
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))

    def test_get_orders_when_customer(self):
        # given
        customer = User.objects.create_user(
            username="customer_user",
            email="customer_user@example.com",
            password="Password123!",
        )

        order = Order.objects.create(user=self.user, total=29.99, date="2024-01-01")
        order2 = Order.objects.create(user=customer, total=15.99, date="2024-01-02")
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        OrderItem.objects.create(order=order, menuitem=menu_item1, quantity=2)
        OrderItem.objects.create(order=order2, menuitem=menu_item1, quantity=1)

        # when
        response = self.client.get("/api/orders/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"]["username"], self.user.username)

    def test_get_orders_when_manager(self):
        # given
        customer = User.objects.create_user(
            username="customer_user",
            email="customer_user@example.com",
            password="Password123!",
        )
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)

        order = Order.objects.create(user=self.user, total=29.99, date="2024-01-01")
        order2 = Order.objects.create(user=customer, total=15.99, date="2024-01-02")
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        OrderItem.objects.create(order=order, menuitem=menu_item1, quantity=2)
        OrderItem.objects.create(order=order2, menuitem=menu_item1, quantity=1)

        # when
        response = self.client.get("/api/orders/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["user"]["username"], self.user.username)
        self.assertEqual(response.data[1]["user"]["username"], customer.username)

    def test_get_orders_when_delivery_crew(self):
        # given
        delivery_person = User.objects.create_user(
            username="delivery_user",
            email="delivery_user@example.com",
            password="Password123!",
        )
        delivery_crew_group = Group.objects.create(name="Delivery Crew")
        delivery_person.groups.add(delivery_crew_group)

        order = Order.objects.create(
            user=self.user,
            total=29.99,
            date="2024-01-01",
            delivery_crew=delivery_person,
        )
        order2 = Order.objects.create(user=self.user, total=15.99, date="2024-01-02")
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        OrderItem.objects.create(order=order, menuitem=menu_item1, quantity=2)
        OrderItem.objects.create(order=order2, menuitem=menu_item1, quantity=1)

        # when
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(
                Token.objects.create(user=delivery_person)
            )
        )
        response = self.client.get("/api/orders/")

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"]["username"], self.user.username)
        self.assertEqual(response.data[0]["delivery_crew"], delivery_person.id)

    def test_create_order(self):
        # given
        main_course_category = Category.objects.create(
            slug="main-course", title="Main Course"
        )
        menu_item1 = MenuItem.objects.create(
            title="Pasta",
            price=12.99,
            featured=False,
            category=main_course_category,
        )
        Cart.objects.create(user=self.user, menuitem=menu_item1, quantity=2)

        # when
        response = self.client.post(
            "/api/orders/",
            {},
            content_type="application/json",
        )

        # then
        self.assertEqual(response.status_code, 201)

    def test_create_order_when_not_customer_forbidden(self):
        for group_name in ["Manager", "Delivery Crew"]:
            with self.subTest(group=group_name):
                # given
                group = Group.objects.create(name=group_name)
                self.user.groups.add(group)

                main_course_category = Category.objects.create(
                    slug="main-course", title="Main Course"
                )
                menu_item1 = MenuItem.objects.create(
                    title="Pasta",
                    price=12.99,
                    featured=False,
                    category=main_course_category,
                )
                Cart.objects.create(user=self.user, menuitem=menu_item1, quantity=2)

                # when
                response = self.client.post(
                    "/api/orders/",
                    {},
                    content_type="application/json",
                )

                # then
                self.assertEqual(response.status_code, 403)

    def test_update_order_when_customer(self):
        # given
        order = Order.objects.create(user=self.user, total=29.99, date="2024-01-01")

        # when
        response = self.client.patch(
            f"/api/orders/{order.id}",
            {"total": 19.99},
            content_type="application/json",
        )

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], "19.99")

    def test_update_order_when_manager_or_delivery_crew_tries_to_update_read_only_field_then_no_change(
        self,
    ):
        for group_name in ["Manager", "Delivery Crew"]:
            with self.subTest(group=group_name):
                # given
                group = Group.objects.create(name=group_name)
                self.user.groups.add(group)
                order = Order.objects.create(
                    user=self.user, total=29.99, date="2024-01-01"
                )

                # when
                response = self.client.patch(
                    f"/api/orders/{order.id}",
                    {"total": 19.99},  # Try to update read-only field
                    content_type="application/json",
                )

                # then
                # NOTE: DRF serializer doesn't raise an error when we try to update read-only fields
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["total"], "29.99")

    def test_update_order_status_when_manager_or_delivery_crew(self):
        for group_name in ["Manager", "Delivery Crew"]:
            with self.subTest(group=group_name):
                # given
                group = Group.objects.create(name=group_name)
                self.user.groups.add(group)
                order = Order.objects.create(
                    user=self.user, total=29.99, date="2024-01-01"
                )

                # when
                response = self.client.patch(
                    f"/api/orders/{order.id}",
                    {"status": 1},
                    content_type="application/json",
                )

                # then
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["status"], 1)

    def test_update_order_delivery_crew_when_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)
        delivery_person = User.objects.create_user(
            username="delivery_user",
            email="delivery_user@example.com",
            password="Password123!",
        )
        delivery_crew_group = Group.objects.create(name="Delivery Crew")
        delivery_person.groups.add(delivery_crew_group)
        order = Order.objects.create(user=self.user, total=29.99, date="2024-01-01")

        # when
        response = self.client.patch(
            f"/api/orders/{order.id}",
            {"delivery_crew": delivery_person.id},
            content_type="application/json",
        )

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_crew"], delivery_person.id)

    def test_delete_order_when_manager(self):
        # given
        manager_group = Group.objects.create(name="Manager")
        self.user.groups.add(manager_group)
        order = Order.objects.create(user=self.user, total=29.99, date="2024-01-01")

        # when
        response = self.client.delete(f"/api/orders/{order.id}")

        # then
        self.assertEqual(response.status_code, 204)

    def test_delete_order_when_not_manager_forbidden(self):
        for group_name in ["Customer", "Delivery Crew"]:
            with self.subTest(group=group_name):
                # given
                if group_name != "Customer":
                    group = Group.objects.create(name=group_name)
                    self.user.groups.add(group)
                order = Order.objects.create(
                    user=self.user, total=29.99, date="2024-01-01"
                )

                # when
                response = self.client.delete(f"/api/orders/{order.id}")

                # then
                self.assertEqual(response.status_code, 403)
