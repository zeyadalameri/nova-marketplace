from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Cart, CartItem
from commerce.services import validate_coupon

from .serializers import CartCouponSerializer, CartItemWriteSerializer, CartQuantitySerializer, CartSerializer


def user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return Cart.objects.prefetch_related(
        "items__product__category",
        "items__product__variants",
        "items__product__images",
        "items__variant",
    ).get(pk=cart.pk)


class CartView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get(self, request):
        return Response(CartSerializer(user_cart(request.user), context={"request": request}).data)


class CartItemCollectionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemWriteSerializer

    def post(self, request):
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = user_cart(request.user)
        product = serializer.validated_data["product"]
        variant = serializer.validated_data.get("variant")
        quantity = serializer.validated_data["quantity"]
        item, created = CartItem.objects.update_or_create(
            cart=cart, product=product, variant=variant, defaults={"quantity": quantity}
        )
        cart = user_cart(request.user)
        return Response(
            CartSerializer(cart, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemDetailView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartQuantitySerializer

    def get_item(self, request, item_id):
        return get_object_or_404(
            CartItem.objects.select_related("product", "variant"), pk=item_id, cart__user=request.user
        )

    def patch(self, request, item_id):
        item = self.get_item(request, item_id)
        serializer = CartQuantitySerializer(data=request.data, context={"item": item})
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        return Response(
            CartSerializer(user_cart(request.user), context={"request": request}).data
        )

    def delete(self, request, item_id):
        self.get_item(request, item_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartCouponView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartCouponSerializer

    def post(self, request):
        serializer = CartCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = user_cart(request.user)
        subtotal = sum(item.line_total_cents for item in cart.items.all())
        first_item = next(iter(cart.items.all()), None)
        if not first_item:
            return Response({"detail": "السلة فارغة."}, status=status.HTTP_400_BAD_REQUEST)
        validate_coupon(serializer.validated_data["code"], request.user, subtotal, first_item.product.currency)
        cart.coupon_code = serializer.validated_data["code"]
        cart.save(update_fields=["coupon_code", "updated_at"])
        return Response(CartSerializer(user_cart(request.user), context={"request": request}).data)

    def delete(self, request):
        cart = user_cart(request.user)
        cart.coupon_code = ""
        cart.save(update_fields=["coupon_code", "updated_at"])
        return Response(CartSerializer(user_cart(request.user), context={"request": request}).data)
