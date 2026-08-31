import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ExchangeRate(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=60)
    rate_from_base = models.DecimalField(
        max_digits=18, decimal_places=8, validators=[MinValueValidator(0.00000001)]
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "نسبة مئوية"
        FIXED = "fixed", "قيمة ثابتة"

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    value = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="SAR")
    minimum_order_cents = models.PositiveBigIntegerField(default=0)
    maximum_discount_cents = models.PositiveBigIntegerField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(default=1)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.currency = self.currency.upper()
        super().save(*args, **kwargs)

    def is_currently_valid(self):
        now = timezone.now()
        return (
            self.is_active
            and (not self.starts_at or self.starts_at <= now)
            and (not self.ends_at or self.ends_at >= now)
        )

    def __str__(self):
        return self.code


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, related_name="redemptions", on_delete=models.PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="coupon_redemptions", on_delete=models.PROTECT
    )
    order = models.OneToOneField(
        "orders.Order", related_name="coupon_redemption", on_delete=models.CASCADE
    )
    discount_cents = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "تم الإنشاء"
        PENDING = "pending", "قيد المعالجة"
        PAID = "paid", "مدفوع"
        FAILED = "failed", "فشل"
        REFUNDED = "refunded", "مسترجع"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey("orders.Order", related_name="payments", on_delete=models.PROTECT)
    provider = models.CharField(max_length=40, default="sandbox")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    amount_cents = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    idempotency_key = models.CharField(max_length=120, unique=True)
    provider_reference = models.CharField(max_length=160, blank=True)
    client_secret = models.CharField(max_length=180, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_payment_per_order")
        ]

    def __str__(self):
        return f"{self.public_id} - {self.status}"


class WebhookEvent(models.Model):
    provider = models.CharField(max_length=40)
    event_id = models.CharField(max_length=160)
    payload_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=30, default="received")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "event_id"], name="unique_provider_event")
        ]
        ordering = ["-created_at"]


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار التجهيز"
        READY = "ready", "جاهز للشحن"
        IN_TRANSIT = "in_transit", "في الطريق"
        DELIVERED = "delivered", "تم التسليم"
        RETURNED = "returned", "مرتجع"
        CANCELLED = "cancelled", "ملغي"

    order = models.OneToOneField("orders.Order", related_name="shipment", on_delete=models.CASCADE)
    provider = models.CharField(max_length=80, default="sandbox")
    tracking_number = models.CharField(max_length=100, unique=True)
    tracking_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    estimated_delivery_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tracking_number


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "تم الطلب"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"
        RECEIVED = "received", "تم الاستلام"
        REFUNDED = "refunded", "تم الاسترجاع"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="return_requests", on_delete=models.PROTECT
    )
    order = models.ForeignKey("orders.Order", related_name="return_requests", on_delete=models.PROTECT)
    item = models.ForeignKey(
        "orders.OrderItem", related_name="return_requests", null=True, blank=True, on_delete=models.PROTECT
    )
    reason = models.TextField(max_length=2000)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.REQUESTED)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE
    )
    kind = models.CharField(max_length=40, default="general")
    title = models.CharField(max_length=160)
    body = models.TextField(max_length=1000)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "-created_at"])]


class PushDevice(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        WEB = "web", "Web"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="push_devices", on_delete=models.CASCADE
    )
    token = models.CharField(max_length=300, unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
