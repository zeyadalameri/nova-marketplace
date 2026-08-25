from rest_framework import serializers

from django.conf import settings
from django.db.models import Avg

from commerce.services import convert_cents

from .models import Category, Favorite, Product, ProductImage, ProductVariant, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image_url", "display_order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    price_cents = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    display_price_cents = serializers.SerializerMethodField()
    display_currency = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "attributes",
            "price_delta_cents",
            "price_cents",
            "display_price_cents",
            "display_currency",
            "stock",
            "is_available",
        ]

    def _currency(self):
        request = self.context.get("request")
        currency = request.query_params.get("currency", "") if request else ""
        return currency.upper() if currency.upper() in settings.SUPPORTED_CURRENCIES else None

    def get_display_price_cents(self, obj) -> int:
        currency = self._currency()
        return convert_cents(obj.price_cents, obj.product.currency, currency) if currency else obj.price_cents

    def get_display_currency(self, obj) -> str:
        return self._currency() or obj.product.currency


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "url", "alt_text", "display_order"]

    def get_url(self, obj) -> str:
        if not obj.image:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    price = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    has_variants = serializers.BooleanField(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    display_price_cents = serializers.SerializerMethodField()
    display_currency = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "brand",
            "sku",
            "description",
            "price_cents",
            "price",
            "currency",
            "display_price_cents",
            "display_currency",
            "stock",
            "image_url",
            "is_featured",
            "is_available",
            "has_variants",
            "variants",
            "images",
            "average_rating",
            "review_count",
            "category",
            "created_at",
            "updated_at",
        ]

    def get_price(self, obj) -> str:
        return f"{obj.price_cents / 100:.2f}"

    def get_average_rating(self, obj) -> float:
        value = obj.reviews.filter(is_approved=True).aggregate(value=Avg("rating"))["value"]
        return round(float(value), 1) if value is not None else 0

    def get_review_count(self, obj) -> int:
        return obj.reviews.filter(is_approved=True).count()

    def _currency(self):
        request = self.context.get("request")
        currency = request.query_params.get("currency", "") if request else ""
        return currency.upper() if currency.upper() in settings.SUPPORTED_CURRENCIES else None

    def get_display_price_cents(self, obj) -> int:
        currency = self._currency()
        return convert_cents(obj.price_cents, obj.currency, currency) if currency else obj.price_cents

    def get_display_currency(self, obj) -> str:
        return self._currency() or obj.currency


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), source="product", write_only=True
    )

    class Meta:
        model = Favorite
        fields = ["id", "product", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_product_id(self, product):
        user = self.context["request"].user
        if Favorite.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("المنتج موجود بالفعل في المفضلة.")
        return product


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    product_slug = serializers.SlugRelatedField(
        queryset=Product.objects.filter(is_active=True), source="product", slug_field="slug"
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "product_slug",
            "user_name",
            "rating",
            "title",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_name", "created_at", "updated_at"]

    def get_user_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.user.username

    def validate(self, attrs):
        request = self.context["request"]
        product = attrs.get("product", getattr(self.instance, "product", None))
        if not self.instance and Review.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError("يمكنك إضافة تقييم واحد فقط لكل منتج.")
        return attrs
