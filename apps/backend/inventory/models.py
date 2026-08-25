from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class InventoryBatch(models.Model):
    product = models.ForeignKey(
        "catalog.Product", related_name="inventory_batches", on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        related_name="inventory_batches",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    lot_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost_cents = models.PositiveBigIntegerField(default=0)
    received_at = models.DateField()
    expires_at = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expires_at", "received_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "variant", "lot_number"], name="unique_inventory_lot"
            )
        ]
        indexes = [
            models.Index(fields=["expires_at", "quantity"]),
            models.Index(fields=["product", "variant", "quantity"]),
        ]

    def clean(self):
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError({"variant": "متغير المنتج لا ينتمي إلى المنتج المحدد."})

    def __str__(self):
        return f"{self.product} - {self.lot_number}"


class InventoryMovement(models.Model):
    class Kind(models.TextChoices):
        OPENING = "opening", "رصيد افتتاحي"
        SALE = "sale", "بيع"
        CANCELLATION = "cancellation", "إلغاء طلب"
        RESTOCK = "restock", "توريد"
        ADJUSTMENT = "adjustment", "تسوية"
        RETURN = "return", "مرتجع"
        EXPIRED = "expired", "إتلاف منتهي"

    product = models.ForeignKey(
        "catalog.Product", related_name="inventory_movements", on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        related_name="inventory_movements",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    batch = models.ForeignKey(
        InventoryBatch,
        related_name="movements",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    order = models.ForeignKey(
        "orders.Order",
        related_name="inventory_movements",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    quantity_delta = models.IntegerField()
    stock_after = models.PositiveIntegerField()
    unit_cost_cents = models.PositiveBigIntegerField(default=0)
    reason = models.CharField(max_length=300, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="inventory_movements",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["product", "variant", "-created_at"]),
            models.Index(fields=["kind", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity_delta=0), name="inventory_movement_nonzero"
            )
        ]

    def __str__(self):
        return f"{self.product} {self.quantity_delta:+d}"


class InventoryAlert(models.Model):
    class Type(models.TextChoices):
        OUT_OF_STOCK = "out_of_stock", "نفاد المخزون"
        LOW_STOCK = "low_stock", "مخزون منخفض"
        EXPIRING = "expiring", "قرب انتهاء الصلاحية"
        EXPIRED = "expired", "منتهي الصلاحية"
        SLOW_MOVING = "slow_moving", "بطيء الحركة"

    class Severity(models.TextChoices):
        INFO = "info", "معلومة"
        WARNING = "warning", "تحذير"
        CRITICAL = "critical", "حرج"

    alert_type = models.CharField(max_length=30, choices=Type.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    product = models.ForeignKey(
        "catalog.Product", related_name="inventory_alerts", on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        related_name="inventory_alerts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    batch = models.ForeignKey(
        InventoryBatch,
        related_name="alerts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    fingerprint = models.CharField(max_length=180, unique=True)
    message = models.CharField(max_length=350)
    is_active = models.BooleanField(default=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="acknowledged_inventory_alerts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-last_seen_at"]
        indexes = [
            models.Index(fields=["is_active", "severity", "-last_seen_at"]),
            models.Index(fields=["product", "alert_type"]),
        ]

    def __str__(self):
        return self.message


class AIInsightReport(models.Model):
    class Source(models.TextChoices):
        LOCAL = "local", "تحليل محلي"
        OPENAI = "openai", "OpenAI"

    source = models.CharField(max_length=20, choices=Source.choices)
    model = models.CharField(max_length=80, blank=True)
    period_days = models.PositiveSmallIntegerField(default=30)
    summary = models.TextField()
    priorities = models.JSONField(default=list)
    opportunities = models.JSONField(default=list)
    risks = models.JSONField(default=list)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="inventory_ai_reports",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_source_display()} - {self.created_at:%Y-%m-%d %H:%M}"
