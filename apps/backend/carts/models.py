from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import Product, ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon_code = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f"Cart #{self.pk} - {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, related_name="cart_items", null=True, blank=True, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                condition=Q(variant__isnull=True),
                name="unique_cart_product_without_variant",
            ),
            models.UniqueConstraint(
                fields=["cart", "variant"],
                condition=Q(variant__isnull=False),
                name="unique_cart_variant",
            ),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="cart_quantity_at_least_one"),
        ]

    @property
    def line_total_cents(self):
        price_cents = self.variant.price_cents if self.variant_id else self.product.price_cents
        return price_cents * self.quantity

    def __str__(self):
        return f"{self.product} x {self.quantity}"
