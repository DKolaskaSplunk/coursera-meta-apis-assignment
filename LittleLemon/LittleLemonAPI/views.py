import datetime

from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import (
    ManagerAllCustomerAndDeliveryCrewReadOnly,
    ManagerOnly,
    OrderListPermission,
)
from .serializers import (
    CartSerializer,
    CategorySerializer,
    MenuItemSerializer,
    OrderItemSerializer,
    ReadOnlyUserIdSerializer,
    UserIdSerializer,
)


class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ManagerAllCustomerAndDeliveryCrewReadOnly]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ManagerAllCustomerAndDeliveryCrewReadOnly]


class MenuItemList(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [ManagerAllCustomerAndDeliveryCrewReadOnly]


class MenuItemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [ManagerAllCustomerAndDeliveryCrewReadOnly]


class GroupMemberList(generics.ListCreateAPIView):
    group_name = None
    serializer_class = UserIdSerializer
    permission_classes = [ManagerOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = Group.objects.get(name=self.group_name)
        group.user_set.add(serializer.data["id"])
        return Response(status=status.HTTP_201_CREATED)

    def get_queryset(self):
        return User.objects.filter(groups__name=self.group_name)


class RemoveGroupMember(generics.RetrieveDestroyAPIView):
    group_name = None
    serializer_class = ReadOnlyUserIdSerializer
    permission_classes = [ManagerOnly]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        group = Group.objects.get(name=self.group_name)
        group.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)

    def get_queryset(self):
        return User.objects.filter(groups__name=self.group_name)


class ManagerList(GroupMemberList):
    group_name = "Manager"


class RemoveManager(RemoveGroupMember):
    group_name = "Manager"


class DeliveryCrewList(GroupMemberList):
    group_name = "Delivery Crew"


class RemoveDeliveryCrew(RemoveGroupMember):
    group_name = "Delivery Crew"


class CartListCreateDelete(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        return self.get_queryset()[0]


class OrderList(generics.ListCreateAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [OrderListPermission]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return OrderItem.objects.all()
        elif user.groups.filter(name="Delivery Crew").exists():
            return OrderItem.objects.filter(order__delivery_crew=user)
        return OrderItem.objects.filter(order__user=user)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)[0]
        order = Order(
            user=request.user,
            delivery_crew=None,
            status=0,
            total=cart.quantity * cart.menuitem.price,
            date=datetime.datetime.now(),
        )
        order_item = OrderItem(
            order=order, menuitem=cart.menuitem, quantity=cart.quantity
        )

        cart.delete()
        order.save()
        order_item.save()

        return Response(status=status.HTTP_201_CREATED)
