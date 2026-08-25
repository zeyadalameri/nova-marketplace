from django.db.models import Q
from rest_framework import permissions, viewsets

from .models import Category, Favorite, Product, Review
from .serializers import CategorySerializer, FavoriteSerializer, ProductSerializer, ReviewSerializer


class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("category").prefetch_related(
            "variants", "images"
        )
        query = self.request.query_params.get("q", "").strip()
        category = self.request.query_params.get("category", "").strip()
        featured = self.request.query_params.get("featured", "").lower()
        ordering = self.request.query_params.get("ordering", "-created_at")
        min_price = self.request.query_params.get("min_price", "").strip()
        max_price = self.request.query_params.get("max_price", "").strip()
        available = self.request.query_params.get("available", "").lower()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(brand__icontains=query)
                | Q(sku__icontains=query)
                | Q(description__icontains=query)
            )
        if category:
            queryset = queryset.filter(category__slug=category)
        if featured in {"1", "true", "yes"}:
            queryset = queryset.filter(is_featured=True)
        if min_price.isdigit():
            queryset = queryset.filter(price_cents__gte=int(min_price))
        if max_price.isdigit():
            queryset = queryset.filter(price_cents__lte=int(max_price))
        if available in {"1", "true", "yes"}:
            queryset = queryset.filter(Q(stock__gt=0) | Q(variants__stock__gt=0)).distinct()

        allowed_ordering = {"price": "price_cents", "-price": "-price_cents", "newest": "-created_at"}
        return queryset.order_by(allowed_ordering.get(ordering, "-created_at"))


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user).select_related("product", "product__category")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Review.objects.filter(is_approved=True).select_related("user", "product")
        product_slug = self.request.query_params.get("product", "").strip()
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
