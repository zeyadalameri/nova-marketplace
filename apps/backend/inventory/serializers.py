from rest_framework import serializers

from catalog.models import Product, ProductVariant

from .models import AIInsightReport, InventoryAlert, InventoryBatch, InventoryMovement


class InventoryBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True, allow_null=True)

    class Meta:
        model = InventoryBatch
        fields = [
            "id",
            "product",
            "product_name",
            "variant",
            "variant_name",
            "lot_number",
            "quantity",
            "unit_cost_cents",
            "received_at",
            "expires_at",
            "notes",
            "created_at",
            "updated_at",
        ]


class InventoryMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True, allow_null=True)
    variant_sku = serializers.CharField(source="variant.sku", read_only=True, allow_null=True)
    order_number = serializers.CharField(source="order.invoice_number", read_only=True, allow_null=True)

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "variant",
            "variant_name",
            "variant_sku",
            "batch",
            "order_number",
            "kind",
            "quantity_delta",
            "stock_after",
            "unit_cost_cents",
            "reason",
            "created_at",
        ]


class InventoryAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True, allow_null=True)

    class Meta:
        model = InventoryAlert
        fields = [
            "id",
            "alert_type",
            "severity",
            "product",
            "product_name",
            "variant",
            "variant_name",
            "batch",
            "message",
            "is_active",
            "acknowledged_at",
            "created_at",
            "last_seen_at",
        ]
        read_only_fields = fields


class InventoryAdjustmentSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True
    )
    quantity_delta = serializers.IntegerField()
    kind = serializers.ChoiceField(
        choices=[
            InventoryMovement.Kind.RESTOCK,
            InventoryMovement.Kind.ADJUSTMENT,
            InventoryMovement.Kind.RETURN,
            InventoryMovement.Kind.EXPIRED,
        ],
        default=InventoryMovement.Kind.ADJUSTMENT,
    )
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)
    lot_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    expires_at = serializers.DateField(required=False, allow_null=True)
    unit_cost_cents = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate(self, attrs):
        variant = attrs.get("variant")
        if variant and variant.product_id != attrs["product"].id:
            raise serializers.ValidationError({"variant": "المتغير لا ينتمي إلى المنتج."})
        if attrs["quantity_delta"] == 0:
            raise serializers.ValidationError({"quantity_delta": "يجب أن تكون الكمية غير صفرية."})
        if attrs.get("expires_at") and not attrs.get("lot_number"):
            raise serializers.ValidationError({"lot_number": "رقم الدفعة مطلوب مع تاريخ الصلاحية."})
        return attrs


class InventoryPeriodSerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=7, max_value=365, required=False, default=30)


class InventoryAIRequestSerializer(InventoryPeriodSerializer):
    focus = serializers.CharField(max_length=500, required=False, allow_blank=True)


class InventoryDashboardSerializer(serializers.Serializer):
    period_days = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
    overview = serializers.DictField()
    stock = serializers.ListField(child=serializers.DictField())
    top_sellers = serializers.ListField(child=serializers.DictField())
    slow_movers = serializers.ListField(child=serializers.DictField())
    movements_by_day = serializers.ListField(child=serializers.DictField())
    recent_movements = serializers.ListField(child=serializers.DictField())
    alerts = serializers.ListField(child=serializers.DictField())
    expiring_batches = serializers.ListField(child=serializers.DictField())


class InventoryAIResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    source = serializers.CharField()
    ai_status = serializers.CharField()
    summary = serializers.CharField()
    priorities = serializers.ListField(child=serializers.DictField())
    opportunities = serializers.ListField(child=serializers.CharField())
    risks = serializers.ListField(child=serializers.CharField())


class AIInsightReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsightReport
        fields = [
            "id",
            "source",
            "model",
            "period_days",
            "summary",
            "priorities",
            "opportunities",
            "risks",
            "created_at",
        ]
