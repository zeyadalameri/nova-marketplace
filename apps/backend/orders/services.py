from django.db import transaction
from django.utils import timezone

from catalog.models import Product, ProductVariant
from commerce.models import Payment, Shipment
from inventory.services import record_order_cancellation, scan_inventory

from .models import Order


def restore_order_inventory(order: Order, *, actor=None, released_at=None) -> bool:
    """Restore an order's reserved stock once. The caller must hold the order row lock."""
    if order.inventory_released_at:
        return False

    items = list(order.items.all())
    product_ids = sorted({item.product_id for item in items if item.product_id})
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=product_ids).order_by("id")
    }
    variant_ids = sorted({item.variant_id for item in items if item.variant_id})
    variants = {
        variant.id: variant
        for variant in ProductVariant.objects.select_for_update()
        .filter(id__in=variant_ids)
        .order_by("id")
    }

    for item in items:
        variant = variants.get(item.variant_id)
        product = products.get(item.product_id)
        if variant:
            variant.stock += item.quantity
            variant.save(update_fields=["stock", "updated_at"])
        elif product:
            product.stock += item.quantity
            product.save(update_fields=["stock", "updated_at"])
        if variant or product:
            record_order_cancellation(
                order=order,
                product=product or variant.product,
                variant=variant,
                quantity=item.quantity,
                stock_after=variant.stock if variant else product.stock,
                actor=actor,
            )

    order.inventory_released_at = released_at or timezone.now()
    return True


@transaction.atomic
def release_expired_order(order_id: int, *, now=None, schedule_scan=True) -> bool:
    current_time = now or timezone.now()
    order = (
        Order.objects.select_for_update()
        .prefetch_related("items")
        .filter(pk=order_id)
        .first()
    )
    if not order:
        return False
    if (
        order.payment_method
        not in {Order.PaymentMethod.CARD, Order.PaymentMethod.BANK_TRANSFER}
        or order.status != Order.Status.PENDING
        or order.payment_status
        not in {Order.PaymentStatus.PENDING, Order.PaymentStatus.UNPAID}
        or order.inventory_released_at
        or not order.reservation_expires_at
        or order.reservation_expires_at > current_time
    ):
        return False

    if not restore_order_inventory(order, released_at=current_time):
        return False
    order.status = Order.Status.CANCELLED
    order.payment_status = Order.PaymentStatus.FAILED
    order.save(
        update_fields=["status", "payment_status", "inventory_released_at", "updated_at"]
    )
    Payment.objects.filter(
        order=order, status__in=[Payment.Status.CREATED, Payment.Status.PENDING]
    ).update(status=Payment.Status.FAILED)
    Shipment.objects.filter(order=order).update(status=Shipment.Status.CANCELLED)
    if schedule_scan:
        transaction.on_commit(lambda: scan_inventory(send_notifications=True))
    return True


def release_expired_reservations(*, now=None, batch_size=100, schedule_scan=True) -> int:
    current_time = now or timezone.now()
    order_ids = list(
        Order.objects.filter(
            payment_method__in=[
                Order.PaymentMethod.CARD,
                Order.PaymentMethod.BANK_TRANSFER,
            ],
            status=Order.Status.PENDING,
            payment_status__in=[
                Order.PaymentStatus.PENDING,
                Order.PaymentStatus.UNPAID,
            ],
            inventory_released_at__isnull=True,
            reservation_expires_at__isnull=False,
            reservation_expires_at__lte=current_time,
        )
        .order_by("reservation_expires_at")
        .values_list("id", flat=True)[:batch_size]
    )
    released = sum(
        release_expired_order(order_id, now=current_time, schedule_scan=False)
        for order_id in order_ids
    )
    if released and schedule_scan:
        scan_inventory(send_notifications=True)
    return released
