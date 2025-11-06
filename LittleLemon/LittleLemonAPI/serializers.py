from rest_framework import serializers

from .models import Cart, Category, MenuItem, Order, OrderItem


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


class CartSerializer(serializers.ModelSerializer):
    user = UserIdSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField("get_unit_price")
    price = serializers.SerializerMethodField("get_price")

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "menuitem_id",
            "menuitem",
            "quantity",
            "unit_price",
            "price",
        ]

    def get_unit_price(self, obj):
        return obj.menuitem.price

    def get_price(self, obj):
        return obj.quantity * self.get_unit_price(obj)


class OrderSerializer(serializers.ModelSerializer):
    user = UserIdSerializer(read_only=True)
    items = serializers.SerializerMethodField("get_items")

    def get_items(self, obj):
        order_items = OrderItem.objects.filter(order=obj)
        return OrderItemSerializer(order_items, many=True).data

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "total", "date", "items"]


class OrderItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField("get_unit_price")
    price = serializers.SerializerMethodField("get_price")

    def get_unit_price(self, obj):
        return obj.menuitem.price

    def get_price(self, obj):
        return obj.quantity * self.get_unit_price(obj)

    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "quantity", "unit_price", "price"]
        read_only_fields = [
            "id",
            "menuitem",
            "quantity",
            "unit_price",
            "price",
        ]
