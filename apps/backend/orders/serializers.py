from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import Address
from carts.models import Cart, CartItem
from catalog.models import Product, ProductVariant
from commerce.models import Coupon, CouponRedemption
from commerce.services import (
    calculate_tax_cents,
    convert_cents,
    create_notification,
    ensure_shipment,
    validate_coupon,
)
from inventory.services import record_order_sale, scan_inventory

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    line_total_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "variant",
            "product_name",
            "product_sku",
            "variant_name",
            "variant_sku",
            "quantity",
            "price_cents",
            "line_total_cents",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipment = serializers.SerializerMethodField()
    latest_payment = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "public_id",
            "status",
            "payment_status",
            "payment_method",
            "full_name",
            "phone",
            "city",
            "address",
            "country_code",
            "region",
            "postal_code",
            "address_line2",
            "notes",
            "currency",
            "subtotal_cents",
            "discount_cents",
            "tax_cents",
            "shipping_cents",
            "total_cents",
            "coupon_code",
            "invoice_number",
            "reservation_expires_at",
            "inventory_released_at",
            "shipment",
            "latest_payment",
            "items",
            "created_at",
            "updated_at",
        ]

    def get_shipment(self, obj) -> dict | None:
        try:
            shipment = obj.shipment
        except obj._meta.apps.get_model("commerce", "Shipment").DoesNotExist:
            return None
        return {
            "provider": shipment.provider,
            "tracking_number": shipment.tracking_number,
            "tracking_url": shipment.tracking_url,
            "status": shipment.status,
            "estimated_delivery_at": shipment.estimated_delivery_at,
        }

    def get_latest_payment(self, obj) -> dict | None:
        payment = obj.payments.first()
        if not payment:
            return None
        return {
            "public_id": payment.public_id,
            "provider": payment.provider,
            "status": payment.status,
            "amount_cents": payment.amount_cents,
        }


class OrderCreateSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.CharField(
        max_length=120, required=False, allow_blank=True, write_only=True
    )
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source="address_reference", required=False, allow_null=True
    )
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, required=False, default=settings.BASE_CURRENCY)

    class Meta:
        model = Order
        fields = [
            "idempotency_key",
            "payment_method",
            "address_id",
            "full_name",
            "phone",
            "city",
            "address",
            "country_code",
            "region",
            "postal_code",
            "address_line2",
            "notes",
            "coupon_code",
            "currency",
        ]
        extra_kwargs = {
            "full_name": {"required": False},
            "phone": {"required": False},
            "city": {"required": False},
            "address": {"required": False},
            "country_code": {"required": False},
            "region": {"required": False},
            "postal_code": {"required": False},
            "address_line2": {"required": False},
        }

    def validate(self, attrs):
        user = self.context["request"].user
        address = attrs.get("address_reference")
        if address and address.user_id != user.id:
            raise serializers.ValidationError({"address_id": "العنوان لا يخص المستخدم الحالي."})
        if not address:
            missing = [field for field in ("full_name", "phone", "city", "address") if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: "هذا الحقل مطلوب عند عدم اختيار عنوان محفوظ." for field in missing})
        currency = attrs.get("currency", settings.BASE_CURRENCY).upper()
        if currency not in settings.SUPPORTED_CURRENCIES:
            raise serializers.ValidationError({"currency": "العملة غير مدعومة."})
        attrs["currency"] = currency
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        idempotency_key = validated_data.pop("idempotency_key", "")
        address_reference = validated_data.get("address_reference")
        if address_reference:
            validated_data.update(
                {
                    "full_name": address_reference.full_name,
                    "phone": address_reference.phone,
                    "city": address_reference.city,
                    "address": address_reference.line1,
                    "country_code": address_reference.country_code,
                    "region": address_reference.region,
                    "postal_code": address_reference.postal_code,
                    "address_line2": address_reference.line2,
                }
            )
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist as exc:
            raise serializers.ValidationError({"cart": "السلة فارغة."}) from exc

        cart_items = list(
            CartItem.objects.filter(cart=cart).select_related("product", "variant")
        )
        if not cart_items:
            raise serializers.ValidationError({"cart": "السلة فارغة."})

        product_ids = [item.product_id for item in cart_items]
        locked_products = {
            product.id: product
            for product in Product.objects.select_for_update()
            .filter(id__in=product_ids)
            .order_by("id")
        }
        variant_ids = [item.variant_id for item in cart_items if item.variant_id]
        locked_variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_for_update()
            .filter(id__in=variant_ids)
            .order_by("id")
        }

        subtotal_cents = 0
        order_currency = validated_data["currency"]
        item_prices = {}
        for item in cart_items:
            product = locked_products.get(item.product_id)
            if not product or not product.is_active:
                raise serializers.ValidationError({"cart": f"المنتج {item.product.name} غير متاح."})
            variant = locked_variants.get(item.variant_id) if item.variant_id else None
            if item.variant_id and (not variant or not variant.is_active or variant.product_id != product.id):
                raise serializers.ValidationError({"cart": f"متغير المنتج {product.name} غير متاح."})
            available_stock = variant.stock if variant else product.stock
            if item.quantity > available_stock:
                raise serializers.ValidationError(
                    {"cart": f"المتوفر من {product.name} هو {available_stock} فقط."}
                )
            source_price = variant.price_cents if variant else product.price_cents
            price_cents = convert_cents(source_price, product.currency, order_currency)
            item_prices[item.id] = price_cents
            subtotal_cents += price_cents * item.quantity

        coupon_code = (validated_data.pop("coupon_code", "") or cart.coupon_code).strip().upper()
        coupon = None
        discount_cents = 0
        if coupon_code:
            Coupon.objects.select_for_update().filter(code=coupon_code).first()
            coupon, discount_cents = validate_coupon(
                coupon_code, user, subtotal_cents, order_currency
            )
        free_shipping_threshold = convert_cents(
            settings.FREE_SHIPPING_THRESHOLD_CENTS,
            settings.BASE_CURRENCY,
            order_currency,
        )
        shipping_base_cents = (
            0
            if subtotal_cents >= free_shipping_threshold
            else settings.DEFAULT_SHIPPING_CENTS
        )
        shipping_cents = convert_cents(
            shipping_base_cents, settings.BASE_CURRENCY, order_currency
        )
        taxable_cents = max(0, subtotal_cents - discount_cents)
        tax_cents = calculate_tax_cents(taxable_cents)
        order = Order.objects.create(
            user=user,
            idempotency_key=idempotency_key,
            subtotal_cents=subtotal_cents,
            discount_cents=discount_cents,
            tax_cents=tax_cents,
            shipping_cents=shipping_cents,
            total_cents=taxable_cents + tax_cents + shipping_cents,
            coupon_code=coupon_code,
            payment_status=(
                Order.PaymentStatus.PENDING
                if validated_data.get("payment_method") == Order.PaymentMethod.CARD
                else Order.PaymentStatus.UNPAID
            ),
            reservation_expires_at=(
                timezone.now() + timedelta(minutes=settings.PAYMENT_RESERVATION_MINUTES)
                if validated_data.get("payment_method")
                in {Order.PaymentMethod.CARD, Order.PaymentMethod.BANK_TRANSFER}
                else None
            ),
            **validated_data,
        )
        order.invoice_number = f"NOVA-{order.created_at:%Y%m}-{order.pk:06d}"
        order.save(update_fields=["invoice_number"])

        order_items = []
        for item in cart_items:
            product = locked_products[item.product_id]
            variant = locked_variants.get(item.variant_id) if item.variant_id else None
            if variant:
                variant.stock -= item.quantity
                variant.save(update_fields=["stock", "updated_at"])
            else:
                product.stock -= item.quantity
                product.save(update_fields=["stock", "updated_at"])
            record_order_sale(
                order=order,
                product=product,
                variant=variant,
                quantity=item.quantity,
                stock_after=variant.stock if variant else product.stock,
            )
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    variant=variant,
                    product_name=product.name,
                    product_sku=product.sku,
                    variant_name=variant.name if variant else "",
                    variant_sku=variant.sku if variant else "",
                    quantity=item.quantity,
                    price_cents=item_prices[item.id],
                )
            )
        OrderItem.objects.bulk_create(order_items)
        if coupon:
            CouponRedemption.objects.create(
                coupon=coupon,
                user=user,
                order=order,
                discount_cents=discount_cents,
            )
        CartItem.objects.filter(cart=cart).delete()
        cart.coupon_code = ""
        cart.save(update_fields=["coupon_code", "updated_at"])
        if order.payment_method == Order.PaymentMethod.CASH_ON_DELIVERY:
            ensure_shipment(order)
        transaction.on_commit(
            lambda: create_notification(
                user,
                "تم استلام طلبك",
                f"استلمنا طلبك {order.invoice_number} وسنحدّثك عند تغير حالته.",
                kind="order",
                data={"order_id": str(order.public_id)},
            )
        )
        transaction.on_commit(lambda: scan_inventory(send_notifications=True))
        return order
