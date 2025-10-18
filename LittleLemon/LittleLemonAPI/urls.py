from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.CategoryList.as_view()),
    path("categories/<int:pk>", views.CategoryDetail.as_view()),
    path("menu-items/", views.MenuItemList.as_view()),
    path("menu-items/<int:pk>", views.MenuItemDetail.as_view()),
    path("groups/manager/users", views.ManagerList.as_view()),
    path("groups/manager/users/<int:pk>", views.RemoveManager.as_view()),
    path("groups/delivery-crew/users", views.DeliveryCrewList.as_view()),
    path("groups/delivery-crew/users/<int:pk>", views.RemoveDeliveryCrew.as_view()),
]
