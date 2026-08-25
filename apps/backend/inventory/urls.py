from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AIInsightReportViewSet,
    InventoryAdjustmentView,
    InventoryAIAnalysisView,
    InventoryAlertViewSet,
    InventoryBatchViewSet,
    InventoryDashboardView,
    InventoryMovementViewSet,
    InventoryScanView,
)

router = DefaultRouter()
router.register("admin/inventory/alerts", InventoryAlertViewSet, basename="inventory-alert")
router.register("admin/inventory/movements", InventoryMovementViewSet, basename="inventory-movement")
router.register("admin/inventory/batches", InventoryBatchViewSet, basename="inventory-batch")
router.register("admin/inventory/reports", AIInsightReportViewSet, basename="inventory-report")

urlpatterns = [
    path("admin/inventory/dashboard/", InventoryDashboardView.as_view(), name="inventory-dashboard"),
    path("admin/inventory/analyze/", InventoryAIAnalysisView.as_view(), name="inventory-analyze"),
    path("admin/inventory/adjust/", InventoryAdjustmentView.as_view(), name="inventory-adjust"),
    path("admin/inventory/scan/", InventoryScanView.as_view(), name="inventory-scan"),
] + router.urls
