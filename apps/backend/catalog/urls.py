from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, FavoriteViewSet, ProductViewSet, ReviewViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("favorites", FavoriteViewSet, basename="favorite")
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = router.urls
