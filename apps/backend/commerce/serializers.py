from rest_framework import serializers

from orders.models import Order, OrderItem

from .models import Notification, Payment, PushDevice, ReturnRequest, Shipment


class StoreConfigSerializer(serializers.Serializer):
    store_name = serializers.CharField()
    base_currency = serializers.CharField()
    supported_currencies = serializers.ListField(child=serializers.CharField())
    supported_languages = serializers.ListField(child=serializers.CharField())
    tax_rate_percent = serializers.FloatField()
    free_shipping_threshold_cents = serializers.IntegerField()
    exchange_rates = serializers.DictField(child=serializers.CharField())
    payment_provider = serializers.CharField()
    shipping_provider = serializers.CharField()


class PaymentWebhookSerializer(serializers.Serializer):
    event_id = serializers.CharField()
    payment_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=["payment.succeeded"])
    amount_cents = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(min_length=3, max_length=3)


class PaymentWebhookResponseSerializer(serializers.Serializer):
    received = serializers.BooleanField()
    processed = serializers.BooleanField()
    status = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="order.public_id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "public_id",
            "order_id",
            "provider",
            "status",
            "amount_cents",
            "currency",
            "provider_reference",
            "client_secret",
            "created_at",
            "updated_at",
        ]


class ShipmentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="order.public_id", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "order_id",
            "provider",
            "tracking_number",
            "tracking_url",
            "status",
            "estimated_delivery_at",
            "shipped_at",
            "delivered_at",
            "updated_at",
        ]


class ReturnRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.SlugRelatedField(
        queryset=Order.objects.all(), source="order", slug_field="public_id"
    )
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(), source="item", allow_null=True, required=False
    )

    class Meta:
        model = ReturnRequest
        fields = [
            "public_id",
            "order_id",
            "item_id",
            "reason",
            "status",
            "resolution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "status", "resolution", "created_at", "updated_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        order = attrs["order"]
        item = attrs.get("item")
        if order.user_id != user.id and not user.is_staff:
            raise serializers.ValidationError("الطلب لا يخص المستخدم الحالي.")
        if order.status not in {Order.Status.DELIVERED, Order.Status.SHIPPED}:
            raise serializers.ValidationError("يمكن طلب الإرجاع بعد شحن الطلب أو تسليمه.")
        if item and item.order_id != order.id:
            raise serializers.ValidationError({"item_id": "العنصر لا ينتمي إلى الطلب."})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "data", "is_read", "created_at"]
        read_only_fields = fields


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = ["id", "token", "platform", "is_active", "updated_at"]
        read_only_fields = ["id", "updated_at"]
