import hashlib
import hmac
import secrets
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Coupon, CouponRedemption, ExchangeRate, Notification, Payment, Shipment, WebhookEvent


def convert_cents(amount_cents: int, from_currency: str, to_currency: str) -> int:
    source = from_currency.upper()
    target = to_currency.upper()
    if source == target:
        return amount_cents

    base = settings.BASE_CURRENCY

    def rate(code: str) -> Decimal:
        if code == base:
            return Decimal("1")
        try:
            return ExchangeRate.objects.get(code=code, is_active=True).rate_from_base
        except ExchangeRate.DoesNotExist as exc:
            raise serializers.ValidationError({"currency": f"لا يتوفر سعر صرف للعملة {code}."}) from exc

    base_amount = Decimal(amount_cents) / rate(source)
    converted = (base_amount * rate(target)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return max(0, int(converted))


def calculate_tax_cents(taxable_cents: int) -> int:
    return max(0, (taxable_cents * settings.TAX_RATE_BPS + 5000) // 10000)


def validate_coupon(code: str, user, subtotal_cents: int, currency: str):
    normalized = code.strip().upper()
    if not normalized:
        return None, 0
    try:
        coupon = Coupon.objects.get(code=normalized)
    except Coupon.DoesNotExist as exc:
        raise serializers.ValidationError({"coupon_code": "رمز الخصم غير صحيح."}) from exc
    if not coupon.is_currently_valid():
        raise serializers.ValidationError({"coupon_code": "رمز الخصم غير فعال أو منتهي."})
    if coupon.usage_limit is not None and coupon.redemptions.count() >= coupon.usage_limit:
        raise serializers.ValidationError({"coupon_code": "تم بلوغ الحد الأقصى لاستخدام الرمز."})
    if coupon.redemptions.filter(user=user).count() >= coupon.per_user_limit:
        raise serializers.ValidationError({"coupon_code": "سبق أن استخدمت هذا الرمز."})

    minimum = convert_cents(coupon.minimum_order_cents, coupon.currency, currency)
    if subtotal_cents < minimum:
        raise serializers.ValidationError({"coupon_code": "قيمة السلة أقل من الحد المطلوب للرمز."})

    if coupon.discount_type == Coupon.DiscountType.PERCENT:
        discount = subtotal_cents * min(coupon.value, 100) // 100
    else:
        discount = convert_cents(coupon.value, coupon.currency, currency)
    if coupon.maximum_discount_cents is not None:
        maximum = convert_cents(coupon.maximum_discount_cents, coupon.currency, currency)
        discount = min(discount, maximum)
    return coupon, min(subtotal_cents, discount)


def create_notification(user, title: str, body: str, *, kind="general", data=None):
    notification = Notification.objects.create(
        user=user, title=title, body=body, kind=kind, data=data or {}
    )
    if user.email:
        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    return notification


def ensure_shipment(order):
    tracking_number = f"NOVA-{str(order.public_id).split('-')[0].upper()}"
    shipment, _ = Shipment.objects.get_or_create(
        order=order,
        defaults={
            "provider": settings.SHIPPING_PROVIDER,
            "tracking_number": tracking_number,
            "tracking_url": f"{settings.PUBLIC_STORE_URL}/orders/{order.public_id}",
            "estimated_delivery_at": timezone.now() + timedelta(days=4),
        },
    )
    return shipment


def initiate_payment(order, idempotency_key: str):
    existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.order_id != order.id:
            raise serializers.ValidationError({"idempotency_key": "المفتاح مستخدم لطلب آخر."})
        return existing
    return Payment.objects.create(
        order=order,
        provider=settings.PAYMENT_PROVIDER,
        status=Payment.Status.PENDING,
        amount_cents=order.total_cents,
        currency=order.currency,
        idempotency_key=idempotency_key,
        provider_reference=f"sandbox_{secrets.token_hex(8)}",
        client_secret=secrets.token_urlsafe(32),
    )


@transaction.atomic
def complete_payment(payment: Payment, *, event_id: str, payload: dict):
    event, created = WebhookEvent.objects.get_or_create(
        provider=payment.provider,
        event_id=event_id,
        defaults={"payload_hash": hashlib.sha256(repr(payload).encode()).hexdigest()},
    )
    if not created and event.status == "processed":
        return payment, False

    payment = Payment.objects.select_for_update().select_related("order", "order__user").get(pk=payment.pk)
    if payment.status == Payment.Status.PAID:
        event.status = "processed"
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "processed_at"])
        return payment, False

    order = payment.order
    payment.status = Payment.Status.PAID
    payment.raw_response = payload
    payment.save(update_fields=["status", "raw_response", "updated_at"])
    order.payment_status = order.PaymentStatus.PAID
    if order.status == order.Status.PENDING:
        order.status = order.Status.CONFIRMED
    order.save(update_fields=["payment_status", "status", "updated_at"])
    ensure_shipment(order)
    event.status = "processed"
    event.processed_at = timezone.now()
    event.save(update_fields=["status", "processed_at"])
    transaction.on_commit(
        lambda: create_notification(
            order.user,
            "تم تأكيد الدفع",
            f"تم استلام دفعة الطلب {order.invoice_number} بنجاح.",
            kind="payment",
            data={"order_id": str(order.public_id)},
        )
    )
    return payment, True


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")
