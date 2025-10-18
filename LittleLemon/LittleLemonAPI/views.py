from django.contrib.auth.models import User, Group
from rest_framework import generics, status
from rest_framework.response import Response

from .models import MenuItem, Category
from .serializers import (
    MenuItemSerializer,
    CategorySerializer,
    UserIdSerializer,
    ReadOnlyUserIdSerializer,
)
from .permissions import ManagerAllCustomerAndDeliveryCrewReadOnly, ManagerOnly


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
