from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from commerce.models import Payment, Shipment
from commerce.serializers import PaymentSerializer, ShipmentSerializer
from commerce.services import create_notification, initiate_payment
from inventory.services import scan_inventory

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from .services import release_expired_order, restore_order_inventory


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = Order.objects.prefetch_related("items", "payments").select_related("shipment")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == "create" else OrderSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        type(request.user).objects.select_for_update().get(pk=request.user.pk)
        key = str(request.headers.get("Idempotency-Key") or request.data.get("idempotency_key") or "").strip()
        if key:
            existing = Order.objects.filter(user=request.user, idempotency_key=key).first()
            if existing:
                return Response(OrderSerializer(existing).data, status=status.HTTP_200_OK)
        data = request.data.copy()
        if key:
            data["idempotency_key"] = key
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, public_id=None):
        order = get_object_or_404(
            self.get_queryset().select_for_update(),
            public_id=public_id,
        )
        if order.status not in {Order.Status.PENDING, Order.Status.CONFIRMED}:
            return Response(
                {"detail": "لا يمكن إلغاء الطلب بعد بدء التجهيز أو الشحن."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        restore_order_inventory(order, actor=request.user)
        order.status = Order.Status.CANCELLED
        if order.payment_status == Order.PaymentStatus.PAID:
            order.payment_status = Order.PaymentStatus.REFUNDED
            Payment.objects.filter(order=order, status=Payment.Status.PAID).update(
                status=Payment.Status.REFUNDED
            )
        elif order.payment_status == Order.PaymentStatus.PENDING:
            order.payment_status = Order.PaymentStatus.FAILED
            Payment.objects.filter(
                order=order, status__in=[Payment.Status.CREATED, Payment.Status.PENDING]
            ).update(status=Payment.Status.FAILED)
        Shipment.objects.filter(order=order).update(status=Shipment.Status.CANCELLED)
        order.save(
            update_fields=["status", "payment_status", "inventory_released_at", "updated_at"]
        )
        transaction.on_commit(
            lambda: create_notification(
                order.user,
                "تم إلغاء الطلب",
                f"تم إلغاء الطلب {order.invoice_number}.",
                kind="order",
                data={"order_id": str(order.public_id)},
            )
        )
        transaction.on_commit(lambda: scan_inventory(send_notifications=True))
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def initiate_payment(self, request, public_id=None):
        order = self.get_object()
        if order.payment_method != Order.PaymentMethod.CARD:
            return Response(
                {"detail": "الطلب لا يستخدم الدفع الإلكتروني."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if release_expired_order(order.pk):
            return Response(
                {"detail": "انتهت مهلة حجز المخزون وأُلغي الطلب."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        if not key:
            return Response(
                {"idempotency_key": "هذا المفتاح مطلوب لمنع تكرار الخصم."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment = initiate_payment(order, str(key))
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def tracking(self, request, public_id=None):
        order = self.get_object()
        try:
            shipment = order.shipment
        except Shipment.DoesNotExist:
            return Response({"detail": "لم يتم إنشاء شحنة بعد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShipmentSerializer(shipment).data)
