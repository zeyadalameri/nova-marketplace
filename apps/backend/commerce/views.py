import json
import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ExchangeRate, Notification, Payment, PushDevice, ReturnRequest, Shipment
from .serializers import (
    NotificationSerializer,
    PaymentSerializer,
    PaymentWebhookResponseSerializer,
    PaymentWebhookSerializer,
    PushDeviceSerializer,
    ReturnRequestSerializer,
    ShipmentSerializer,
    StoreConfigSerializer,
)
from .services import complete_payment, verify_webhook_signature


class StoreConfigView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StoreConfigSerializer

    def get(self, request):
        rates = {settings.BASE_CURRENCY: "1"}
        rates.update(
            {
                rate.code: str(rate.rate_from_base)
                for rate in ExchangeRate.objects.filter(is_active=True)
            }
        )
        return Response(
            {
                "store_name": "NOVA Marketplace",
                "base_currency": settings.BASE_CURRENCY,
                "supported_currencies": settings.SUPPORTED_CURRENCIES,
                "supported_languages": settings.SUPPORTED_LANGUAGES,
                "tax_rate_percent": settings.TAX_RATE_BPS / 100,
                "free_shipping_threshold_cents": settings.FREE_SHIPPING_THRESHOLD_CENTS,
                "exchange_rates": rates,
                "payment_provider": settings.PAYMENT_PROVIDER,
                "shipping_provider": settings.SHIPPING_PROVIDER,
            }
        )


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    def get_queryset(self):
        queryset = Payment.objects.select_related("order", "order__user")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        return queryset if self.request.user.is_staff else queryset.filter(order__user=self.request.user)

    @action(detail=True, methods=["post"])
    def sandbox_confirm(self, request, public_id=None):
        if settings.PAYMENT_PROVIDER != "sandbox":
            return Response(
                {"detail": "التأكيد التجريبي غير متاح مع مزود الإنتاج."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment = self.get_object()
        payment, _ = complete_payment(
            payment,
            event_id=f"manual-{uuid.uuid4()}",
            payload={"type": "payment.succeeded", "payment_id": str(payment.public_id)},
        )
        return Response(PaymentSerializer(payment).data)


class PaymentWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = PaymentWebhookSerializer

    @extend_schema(request=PaymentWebhookSerializer, responses=PaymentWebhookResponseSerializer)
    def post(self, request):
        signature = request.headers.get("X-Nova-Signature", "")
        if not verify_webhook_signature(request.body, signature):
            return Response({"detail": "توقيع Webhook غير صالح."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = json.loads(request.body.decode("utf-8"))
            payment = Payment.objects.get(public_id=payload["payment_id"])
            event_id = str(payload["event_id"])
        except (ValueError, KeyError, Payment.DoesNotExist):
            return Response({"detail": "بيانات Webhook غير صالحة."}, status=status.HTTP_400_BAD_REQUEST)
        payment, processed = complete_payment(payment, event_id=event_id, payload=payload)
        return Response({"received": True, "processed": processed, "status": payment.status})


class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "tracking_number"

    def get_queryset(self):
        queryset = Shipment.objects.select_related("order", "order__user")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        return queryset if self.request.user.is_staff else queryset.filter(order__user=self.request.user)


class ReturnRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = ReturnRequest.objects.select_related("order", "item", "user")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        return queryset if self.request.user.is_staff else queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})


class PushDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = PushDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return PushDevice.objects.none()
        return PushDevice.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device, _ = PushDevice.objects.update_or_create(
            token=serializer.validated_data["token"],
            defaults={
                "user": request.user,
                "platform": serializer.validated_data["platform"],
                "is_active": serializer.validated_data.get("is_active", True),
            },
        )
        return Response(PushDeviceSerializer(device).data, status=status.HTTP_201_CREATED)
