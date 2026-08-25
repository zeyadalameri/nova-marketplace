from rest_framework import serializers

from django.conf import settings
from rest_framework.exceptions import ValidationError

from catalog.models import Product, ProductVariant
from catalog.serializers import ProductSerializer, ProductVariantSerializer
from commerce.services import calculate_tax_cents, validate_coupon

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    line_total_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "variant", "quantity", "line_total_cents"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    subtotal_cents = serializers.SerializerMethodField()
    discount_cents = serializers.SerializerMethodField()
    tax_cents = serializers.SerializerMethodField()
    shipping_cents = serializers.SerializerMethodField()
    total_cents = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "item_count",
            "subtotal_cents",
            "discount_cents",
            "tax_cents",
            "shipping_cents",
            "total_cents",
            "currency",
            "coupon_code",
            "updated_at",
        ]

    def get_item_count(self, obj) -> int:
        return sum(item.quantity for item in obj.items.all())

    def get_subtotal_cents(self, obj) -> int:
        return self._quote(obj)["subtotal_cents"]

    def _quote(self, obj):
        cache = self.context.setdefault("_cart_quotes", {})
        if obj.pk in cache:
            return cache[obj.pk]
        subtotal = sum(item.line_total_cents for item in obj.items.all())
        first_item = next(iter(obj.items.all()), None)
        currency = first_item.product.currency if first_item else settings.BASE_CURRENCY
        discount = 0
        if obj.coupon_code and self.context.get("request"):
            try:
                _, discount = validate_coupon(
                    obj.coupon_code, self.context["request"].user, subtotal, currency
                )
            except ValidationError:
                discount = 0
        taxable = max(0, subtotal - discount)
        tax = calculate_tax_cents(taxable)
        shipping = 0 if subtotal >= settings.FREE_SHIPPING_THRESHOLD_CENTS else (
            settings.DEFAULT_SHIPPING_CENTS if subtotal else 0
        )
        cache[obj.pk] = {
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "tax_cents": tax,
            "shipping_cents": shipping,
            "total_cents": taxable + tax + shipping,
            "currency": currency,
        }
        return cache[obj.pk]

    def get_discount_cents(self, obj) -> int:
        return self._quote(obj)["discount_cents"]

    def get_tax_cents(self, obj) -> int:
        return self._quote(obj)["tax_cents"]

    def get_shipping_cents(self, obj) -> int:
        return self._quote(obj)["shipping_cents"]

    def get_total_cents(self, obj) -> int:
        return self._quote(obj)["total_cents"]

    def get_currency(self, obj) -> str:
        return self._quote(obj)["currency"]


class CartItemWriteSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), source="product"
    )
    quantity = serializers.IntegerField(min_value=1, max_value=99)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(is_active=True),
        source="variant",
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        product = attrs["product"]
        variant = attrs.get("variant")
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({"variant_id": "المتغير لا ينتمي إلى المنتج."})
        if not variant and product.variants.filter(is_active=True).exists():
            raise serializers.ValidationError({"variant_id": "اختر أحد متغيرات المنتج."})
        available_stock = variant.stock if variant else product.stock
        if attrs["quantity"] > available_stock:
            raise serializers.ValidationError({"quantity": "الكمية المطلوبة أكبر من المخزون المتاح."})
        return attrs


class CartQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=99)

    def validate_quantity(self, quantity):
        item = self.context["item"]
        available_stock = item.variant.stock if item.variant_id else item.product.stock
        if quantity > available_stock:
            raise serializers.ValidationError("الكمية المطلوبة أكبر من المخزون المتاح.")
        return quantity


class CartCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)

    def validate_code(self, value):
        return value.strip().upper()
