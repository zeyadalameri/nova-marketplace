from django.urls import path

from .views import CartCouponView, CartItemCollectionView, CartItemDetailView, CartView

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart-detail"),
    path("cart/items/", CartItemCollectionView.as_view(), name="cart-item-collection"),
    path("cart/items/<int:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/coupon/", CartCouponView.as_view(), name="cart-coupon"),
]
