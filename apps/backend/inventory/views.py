from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIInsightReport, InventoryAlert, InventoryBatch, InventoryMovement
from .serializers import (
    AIInsightReportSerializer,
    InventoryAdjustmentSerializer,
    InventoryAIRequestSerializer,
    InventoryAIResponseSerializer,
    InventoryAlertSerializer,
    InventoryBatchSerializer,
    InventoryDashboardSerializer,
    InventoryMovementSerializer,
    InventoryPeriodSerializer,
)
from .services import adjust_stock, build_inventory_dashboard, generate_inventory_insight, scan_inventory


class StaffOnlyMixin:
    permission_classes = [permissions.IsAdminUser]


class InventoryDashboardView(StaffOnlyMixin, generics.GenericAPIView):
    serializer_class = InventoryPeriodSerializer

    @extend_schema(responses=InventoryDashboardSerializer)
    def get(self, request):
        query = self.get_serializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        scan_inventory(send_notifications=False)
        dashboard = build_inventory_dashboard(query.validated_data["days"])
        return Response(dashboard)


class InventoryAIAnalysisView(StaffOnlyMixin, generics.GenericAPIView):
    serializer_class = InventoryAIRequestSerializer

    @extend_schema(responses=InventoryAIResponseSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scan_inventory(send_notifications=False)
        dashboard = build_inventory_dashboard(serializer.validated_data["days"])
        result = generate_inventory_insight(
            dashboard=dashboard,
            user=request.user,
            focus=serializer.validated_data.get("focus", ""),
        )
        return Response(result)


class InventoryAdjustmentView(StaffOnlyMixin, generics.GenericAPIView):
    serializer_class = InventoryAdjustmentSerializer

    @extend_schema(responses={201: InventoryMovementSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movement = adjust_stock(actor=request.user, **serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        scan_inventory(send_notifications=True)
        return Response(InventoryMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class InventoryScanView(StaffOnlyMixin, generics.GenericAPIView):
    serializer_class = InventoryPeriodSerializer

    @extend_schema(request=None, responses=InventoryDashboardSerializer)
    def post(self, request):
        scan_inventory(send_notifications=True)
        return Response(build_inventory_dashboard(30))


class InventoryAlertViewSet(StaffOnlyMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryAlertSerializer
    queryset = InventoryAlert.objects.select_related("product", "variant", "batch")

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save(update_fields=["acknowledged_at", "acknowledged_by", "last_seen_at"])
        return Response(self.get_serializer(alert).data)


class InventoryMovementViewSet(StaffOnlyMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryMovementSerializer
    queryset = InventoryMovement.objects.select_related("product", "variant", "batch", "order")
    filterset_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get("product")
        kind = self.request.query_params.get("kind")
        if product:
            queryset = queryset.filter(product_id=product)
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset


class InventoryBatchViewSet(StaffOnlyMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryBatchSerializer
    queryset = InventoryBatch.objects.select_related("product", "variant")


class AIInsightReportViewSet(StaffOnlyMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AIInsightReportSerializer
    queryset = AIInsightReport.objects.select_related("generated_by")
