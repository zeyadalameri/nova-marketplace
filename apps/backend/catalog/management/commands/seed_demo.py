from django.core.management.base import BaseCommand
from django.utils import timezone

from datetime import timedelta

from commerce.models import Coupon, ExchangeRate

from catalog.models import Category, Product, ProductVariant
from inventory.models import InventoryBatch, InventoryMovement
from inventory.services import scan_inventory


class Command(BaseCommand):
    help = "Create an idempotent marketplace demo catalog."

    def handle(self, *args, **options):
        category_rows = [
            ("electronics", "الإلكترونيات", "جوالات وصوتيات وأجهزة ذكية", 1),
            ("computers", "الكمبيوتر والألعاب", "أجهزة وملحقات للعمل واللعب", 2),
            ("home", "المنزل والإضاءة", "اختيارات تجعل منزلك أجمل", 3),
            ("kitchen", "المطبخ", "أجهزة عملية لمطبخك اليومي", 4),
            ("fashion", "الأزياء", "ملابس وإكسسوارات لكل يوم", 5),
            ("sports", "الرياضة", "مستلزمات الحركة واللياقة", 6),
            ("travel", "السفر والحقائب", "حقائب وتجهيزات لكل رحلة", 7),
            ("office", "المكتب والدراسة", "منتجات للعمل والتعلّم", 8),
        ]
        categories = {}
        for slug, name, description, display_order in category_rows:
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "display_order": display_order,
                    "is_active": True,
                },
            )
            categories[slug] = category

        products = [
            ("electronics", "سماعة لاسلكية عازلة للضوضاء", "wireless-headphones", "NOVA-001", 29900, 18, "NOVA Audio", "صوت محيطي وبطارية تدوم حتى 38 ساعة مع وسائد مريحة."),
            ("computers", "لوحة مفاتيح ميكانيكية", "mechanical-keyboard", "NOVA-002", 24900, 8, "KeyLab", "مفاتيح هادئة وإضاءة قابلة للتخصيص واتصال سريع."),
            ("electronics", "ساعة ذكية للياقة", "smart-watch", "NOVA-003", 45900, 10, "NOVA Wear", "تتبع للنشاط والنوم والنبض مع مقاومة للماء."),
            ("home", "مصباح مكتبي ذكي", "smart-desk-lamp", "NOVA-004", 18900, 16, "Luma", "إضاءة هادئة بثلاث درجات وتحكم لمسي وتصميم عصري."),
            ("fashion", "قميص قطني مريح", "cotton-shirt", "NOVA-005", 12900, 0, "NOVA Basics", "قطن ناعم بقصة يومية وألوان سهلة التنسيق."),
            ("travel", "حقيبة سفر صلبة 24 بوصة", "travel-suitcase", "NOVA-006", 38900, 7, "Nomad", "هيكل خفيف وعجلات مرنة وقفل رقمي لرحلة أكثر راحة."),
            ("computers", "لابتوب خفيف 14 بوصة", "compact-laptop", "NOVA-007", 279900, 9, "Orbit", "شاشة واضحة وأداء سريع للدراسة والعمل اليومي بوزن خفيف."),
            ("sports", "حذاء جري يومي", "running-shoes", "NOVA-008", 23900, 21, "Stride", "بطانة مرنة وتهوية ممتازة للمشي والتمارين اليومية."),
            ("kitchen", "آلة إسبريسو منزلية", "espresso-machine", "NOVA-009", 64900, 6, "Brewly", "قهوة غنية خلال دقائق مع عصا تبخير وحجم مناسب للمطبخ."),
            ("electronics", "هاتف NOVA X بشاشة OLED", "nova-phone-x", "NOVA-010", 219900, 14, "NOVA Mobile", "شاشة OLED وكاميرا ذكية وبطارية ليوم كامل."),
            ("kitchen", "قلاية هوائية رقمية", "air-fryer", "NOVA-011", 32900, 13, "Culina", "طهي أسرع بزيت أقل وسعة مناسبة للعائلة."),
            ("office", "حقيبة ظهر للعمل والدراسة", "city-backpack", "NOVA-012", 17900, 17, "Carry", "جيوب منظمة ومساحة للابتوب مع أحزمة مريحة."),
            ("electronics", "سماعات أذن لاسلكية", "wireless-earbuds", "NOVA-013", 19900, 26, "NOVA Audio", "حجم صغير وصوت واضح ومقاومة لرذاذ الماء."),
            ("computers", "جهاز لوحي 11 بوصة", "nova-tablet", "NOVA-014", 129900, 11, "Orbit", "شاشة واسعة للترفيه والدراسة مع بطارية طويلة."),
            ("home", "مصباح جانبي هادئ", "ambient-table-lamp", "NOVA-015", 14900, 23, "Luma", "إضاءة دافئة وتصميم بسيط يناسب غرفة النوم والمجلس."),
            ("sports", "حذاء تدريب خفيف", "training-shoes", "NOVA-016", 26900, 12, "Stride", "ثبات ومرونة للتمارين والنشاط اليومي."),
            ("travel", "حقيبة ظهر للسفر الخفيف", "travel-backpack", "NOVA-017", 22900, 5, "Nomad", "سعة عملية وتنظيم داخلي للرحلات القصيرة."),
            ("office", "لوحة مفاتيح مكتبية صغيرة", "compact-keyboard", "NOVA-018", 16900, 19, "KeyLab", "تصميم مدمج يوفر المساحة مع اتصال لاسلكي موثوق."),
        ]
        seeded = {}
        for category_slug, name, slug, sku, price_cents, stock, brand, description in products:
            product, _ = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "category": categories[category_slug],
                    "name": name,
                    "slug": slug,
                    "price_cents": price_cents,
                    "stock": stock,
                    "low_stock_threshold": 8 if sku == "NOVA-006" else 5,
                    "reorder_quantity": 24,
                    "brand": brand,
                    "description": description,
                    "is_active": True,
                    "is_featured": sku in {"NOVA-001", "NOVA-006", "NOVA-007", "NOVA-009", "NOVA-010", "NOVA-011"},
                },
            )
            seeded[sku] = product

        shirt = seeded["NOVA-005"]
        for size, stock in (("S", 5), ("M", 8), ("L", 6), ("XL", 4)):
            ProductVariant.objects.update_or_create(
                sku=f"NOVA-005-{size}",
                defaults={
                    "product": shirt,
                    "name": f"المقاس {size}",
                    "attributes": {"size": size, "color": "أبيض"},
                    "stock": stock,
                    "low_stock_threshold": 5 if size == "XL" else 3,
                    "reorder_quantity": 12,
                    "is_active": True,
                },
            )

        Coupon.objects.update_or_create(
            code="WELCOME10",
            defaults={
                "discount_type": Coupon.DiscountType.PERCENT,
                "value": 10,
                "minimum_order_cents": 10000,
                "maximum_discount_cents": 5000,
                "usage_limit": 1000,
                "per_user_limit": 1,
                "is_active": True,
            },
        )
        ExchangeRate.objects.update_or_create(
            code="USD", defaults={"name": "US Dollar", "rate_from_base": "0.26666667"}
        )
        ExchangeRate.objects.update_or_create(
            code="AED", defaults={"name": "UAE Dirham", "rate_from_base": "0.97933333"}
        )
        for product in seeded.values():
            if product.has_variants:
                for variant in product.variants.filter(is_active=True):
                    if not InventoryMovement.objects.filter(product=product, variant=variant).exists():
                        InventoryMovement.objects.create(
                            product=product,
                            variant=variant,
                            kind=InventoryMovement.Kind.OPENING,
                            quantity_delta=variant.stock,
                            stock_after=variant.stock,
                            reason="رصيد البيانات التجريبية",
                        )
            elif product.stock and not InventoryMovement.objects.filter(
                product=product, variant__isnull=True
            ).exists():
                InventoryMovement.objects.create(
                    product=product,
                    kind=InventoryMovement.Kind.OPENING,
                    quantity_delta=product.stock,
                    stock_after=product.stock,
                    reason="رصيد البيانات التجريبية",
                )

        travel_bag = seeded["NOVA-006"]
        InventoryBatch.objects.update_or_create(
            product=travel_bag,
            variant=None,
            lot_number="DEMO-TRAVEL-01",
            defaults={
                "quantity": 3,
                "unit_cost_cents": 21000,
                "received_at": timezone.localdate(),
                "expires_at": timezone.localdate() + timedelta(days=20),
                "notes": "دفعة تجريبية لاختبار تنبيه الصلاحية",
            },
        )
        scan_inventory(send_notifications=False)
        self.stdout.write(self.style.SUCCESS("Demo catalog is ready."))
