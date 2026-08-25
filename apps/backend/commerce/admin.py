from django.contrib import admin

from .models import (
    Coupon,
    CouponRedemption,
    ExchangeRate,
    Notification,
    Payment,
    PushDevice,
    ReturnRequest,
    Shipment,
    WebhookEvent,
)

admin.site.register(ExchangeRate)
admin.site.register(Coupon)
admin.site.register(CouponRedemption)
admin.site.register(Payment)
admin.site.register(WebhookEvent)
admin.site.register(Shipment)
admin.site.register(ReturnRequest)
admin.site.register(Notification)
admin.site.register(PushDevice)
