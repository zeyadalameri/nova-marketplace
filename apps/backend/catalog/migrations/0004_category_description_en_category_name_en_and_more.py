from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_product_low_stock_threshold_product_reorder_quantity_and_more")]

    operations = [
        migrations.AddField(
            model_name="category",
            name="description_en",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="category",
            name="name_en",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="product",
            name="description_en",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="product",
            name="name_en",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="productvariant",
            name="name_en",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
