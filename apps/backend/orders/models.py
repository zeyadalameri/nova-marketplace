import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from accounts.models import Address
from catalog.models import Product, ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار المراجعة"
        CONFIRMED = "confirmed", "تم التأكيد"
        PROCESSING = "processing", "قيد التجهيز"
        SHIPPED = "shipped", "تم الشحن"
        DELIVERED = "delivered", "تم التسليم"
        CANCELLED = "cancelled", "ملغي"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "غير مدفوع"
        PENDING = "pending", "قيد المعالجة"
        PAID = "paid", "مدفوع"
        FAILED = "failed", "فشل الدفع"
        REFUNDED = "refunded", "مسترجع"

    class PaymentMethod(models.TextChoices):
        CARD = "card", "بطاقة أو محفظة رقمية"
        CASH_ON_DELIVERY = "cod", "الدفع عند الاستلام"
        BANK_TRANSFER = "bank", "تحويل بنكي"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120, blank=True)
    address_reference = models.ForeignKey(
        Address, related_name="orders", null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(
        max_length=30, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    payment_method = models.CharField(
        max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.CASH_ON_DELIVERY
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=300)
    country_code = models.CharField(max_length=2, default="SA")
    region = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    address_line2 = models.CharField(max_length=220, blank=True)
    notes = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    subtotal_cents = models.PositiveBigIntegerField(default=0)
    discount_cents = models.PositiveBigIntegerField(default=0)
    tax_cents = models.PositiveBigIntegerField(default=0)
    shipping_cents = models.PositiveBigIntegerField(default=0)
    total_cents = models.PositiveBigIntegerField(default=0)
    coupon_code = models.CharField(max_length=40, blank=True)
    invoice_number = models.CharField(max_length=40, unique=True, null=True, blank=True)
    reservation_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    inventory_released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="unique_user_checkout_idempotency_key",
            )
        ]
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"Order {self.public_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", null=True, on_delete=models.SET_NULL)
    variant = models.ForeignKey(
        ProductVariant, related_name="order_items", null=True, blank=True, on_delete=models.SET_NULL
    )
    product_name = models.CharField(max_length=150)
    product_sku = models.CharField(max_length=60)
    variant_name = models.CharField(max_length=120, blank=True)
    variant_sku = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField()
    price_cents = models.PositiveBigIntegerField()

    @property
    def line_total_cents(self):
        return self.quantity * self.price_cents

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
