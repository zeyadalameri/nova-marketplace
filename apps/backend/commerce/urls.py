from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationViewSet,
    PaymentViewSet,
    PaymentWebhookView,
    PushDeviceViewSet,
    ReturnRequestViewSet,
    ShipmentViewSet,
    StoreConfigView,
)

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
router.register("shipments", ShipmentViewSet, basename="shipment")
router.register("returns", ReturnRequestViewSet, basename="return-request")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("devices", PushDeviceViewSet, basename="push-device")

urlpatterns = [
    path("store/config/", StoreConfigView.as_view(), name="store-config"),
    path("webhooks/payments/sandbox/", PaymentWebhookView.as_view(), name="payment-webhook"),
] + router.urls
