from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("orders", "0002_order_address_line2_order_address_reference_and_more")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(
                fields=("user", "idempotency_key"),
                condition=~Q(idempotency_key=""),
                name="unique_user_checkout_idempotency_key",
            ),
        ),
    ]
