from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "product_sku", "quantity", "price_cents")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "user",
        "status",
        "payment_status",
        "invoice_number",
        "total_cents",
        "created_at",
    )
    list_filter = ("status", "payment_status", "payment_method")
    search_fields = ("public_id", "user__email", "full_name", "phone")
    readonly_fields = (
        "public_id",
        "invoice_number",
        "subtotal_cents",
        "discount_cents",
        "tax_cents",
        "shipping_cents",
        "total_cents",
        "created_at",
    )
    inlines = [OrderItemInline]
