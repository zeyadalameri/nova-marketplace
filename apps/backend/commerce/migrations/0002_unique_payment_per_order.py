from django.db import migrations, models
from django.db.models import Count


def reject_existing_duplicate_payments(apps, schema_editor):
    payment = apps.get_model("commerce", "Payment")
    duplicate_order = (
        payment.objects.values("order_id")
        .annotate(payment_count=Count("id"))
        .filter(payment_count__gt=1)
        .order_by("order_id")
        .first()
    )
    if duplicate_order:
        raise RuntimeError(
            "Cannot enforce one payment per order: duplicate payments already exist for "
            f"order_id={duplicate_order['order_id']}. Resolve them before migrating."
        )


class Migration(migrations.Migration):
    dependencies = [("commerce", "0001_initial")]

    operations = [
        migrations.RunPython(reject_existing_duplicate_payments, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(
                fields=("order",), name="unique_payment_per_order"
            ),
        ),
    ]
