from rest_framework import serializers
from .models import MenuItem, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category_id", "category"]


class UserIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(max_length=255, read_only=True)


class ReadOnlyUserIdSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=255, read_only=True)
