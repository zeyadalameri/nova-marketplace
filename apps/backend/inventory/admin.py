from django.contrib import admin

from .models import AIInsightReport, InventoryAlert, InventoryBatch, InventoryMovement


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ("product", "variant", "lot_number", "quantity", "expires_at", "received_at")
    list_filter = ("expires_at", "received_at")
    search_fields = ("product__name", "product__sku", "variant__sku", "lot_number")


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "variant", "kind", "quantity_delta", "stock_after", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("product__name", "product__sku", "variant__sku", "order__invoice_number")
    readonly_fields = ("created_at",)


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ("product", "variant", "alert_type", "severity", "is_active", "last_seen_at")
    list_filter = ("alert_type", "severity", "is_active")
    search_fields = ("product__name", "product__sku", "message")


@admin.register(AIInsightReport)
class AIInsightReportAdmin(admin.ModelAdmin):
    list_display = ("source", "model", "period_days", "generated_by", "created_at")
    list_filter = ("source", "created_at")
    readonly_fields = ("summary", "priorities", "opportunities", "risks", "created_at")
