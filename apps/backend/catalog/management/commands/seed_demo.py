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
            ("electronics", "الإلكترونيات", "Electronics", "جوالات وصوتيات وأجهزة ذكية", "Phones, audio, and smart devices", 1),
            ("computers", "الكمبيوتر والألعاب", "Computers & Gaming", "أجهزة وملحقات للعمل واللعب", "Devices and accessories for work and play", 2),
            ("home", "المنزل والإضاءة", "Home & Lighting", "اختيارات تجعل منزلك أجمل", "Selections that make your home better", 3),
            ("kitchen", "المطبخ", "Kitchen", "أجهزة عملية لمطبخك اليومي", "Practical appliances for your everyday kitchen", 4),
            ("fashion", "الأزياء", "Fashion", "ملابس وإكسسوارات لكل يوم", "Everyday clothing and accessories", 5),
            ("sports", "الرياضة", "Sports", "مستلزمات الحركة واللياقة", "Fitness and active-lifestyle essentials", 6),
            ("travel", "السفر والحقائب", "Travel & Luggage", "حقائب وتجهيزات لكل رحلة", "Bags and essentials for every trip", 7),
            ("office", "المكتب والدراسة", "Office & Study", "منتجات للعمل والتعلّم", "Products for work and learning", 8),
        ]
        categories = {}
        for slug, name, name_en, description, description_en, display_order in category_rows:
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "name_en": name_en,
                    "description": description,
                    "description_en": description_en,
                    "display_order": display_order,
                    "is_active": True,
                },
            )
            categories[slug] = category

        products = [
            ("electronics", "سماعة لاسلكية عازلة للضوضاء", "Noise-Cancelling Wireless Headphones", "wireless-headphones", "NOVA-001", 29900, 18, "NOVA Audio", "صوت محيطي وبطارية تدوم حتى 38 ساعة مع وسائد مريحة.", "Immersive sound, up to 38 hours of battery life, and comfortable ear cushions."),
            ("computers", "لوحة مفاتيح ميكانيكية", "Mechanical Keyboard", "mechanical-keyboard", "NOVA-002", 24900, 8, "KeyLab", "مفاتيح هادئة وإضاءة قابلة للتخصيص واتصال سريع.", "Quiet switches, customizable lighting, and a responsive connection."),
            ("electronics", "ساعة ذكية للياقة", "Fitness Smartwatch", "smart-watch", "NOVA-003", 45900, 10, "NOVA Wear", "تتبع للنشاط والنوم والنبض مع مقاومة للماء.", "Activity, sleep, and heart-rate tracking with water resistance."),
            ("home", "مصباح مكتبي ذكي", "Smart Desk Lamp", "smart-desk-lamp", "NOVA-004", 18900, 16, "Luma", "إضاءة هادئة بثلاث درجات وتحكم لمسي وتصميم عصري.", "Three comfortable light levels, touch controls, and a modern design."),
            ("fashion", "قميص قطني مريح", "Comfortable Cotton Shirt", "cotton-shirt", "NOVA-005", 12900, 0, "NOVA Basics", "قطن ناعم بقصة يومية وألوان سهلة التنسيق.", "Soft cotton, an everyday fit, and easy-to-match colors."),
            ("travel", "حقيبة سفر صلبة 24 بوصة", "24-inch Hardshell Suitcase", "travel-suitcase", "NOVA-006", 38900, 7, "Nomad", "هيكل خفيف وعجلات مرنة وقفل رقمي لرحلة أكثر راحة.", "A lightweight shell, smooth wheels, and a digital lock for easier travel."),
            ("computers", "لابتوب خفيف 14 بوصة", "Lightweight 14-inch Laptop", "compact-laptop", "NOVA-007", 279900, 9, "Orbit", "شاشة واضحة وأداء سريع للدراسة والعمل اليومي بوزن خفيف.", "A crisp display and fast everyday performance in a lightweight design."),
            ("sports", "حذاء جري يومي", "Everyday Running Shoes", "running-shoes", "NOVA-008", 23900, 21, "Stride", "بطانة مرنة وتهوية ممتازة للمشي والتمارين اليومية.", "Flexible cushioning and excellent ventilation for walking and daily exercise."),
            ("kitchen", "آلة إسبريسو منزلية", "Home Espresso Machine", "espresso-machine", "NOVA-009", 64900, 6, "Brewly", "قهوة غنية خلال دقائق مع عصا تبخير وحجم مناسب للمطبخ.", "Rich coffee in minutes with a steam wand and a kitchen-friendly footprint."),
            ("electronics", "هاتف NOVA X بشاشة OLED", "NOVA X OLED Smartphone", "nova-phone-x", "NOVA-010", 219900, 14, "NOVA Mobile", "شاشة OLED وكاميرا ذكية وبطارية ليوم كامل.", "An OLED display, smart camera, and all-day battery life."),
            ("kitchen", "قلاية هوائية رقمية", "Digital Air Fryer", "air-fryer", "NOVA-011", 32900, 13, "Culina", "طهي أسرع بزيت أقل وسعة مناسبة للعائلة.", "Faster cooking with less oil and a family-friendly capacity."),
            ("office", "حقيبة ظهر للعمل والدراسة", "Work and Study Backpack", "city-backpack", "NOVA-012", 17900, 17, "Carry", "جيوب منظمة ومساحة للابتوب مع أحزمة مريحة.", "Organized pockets, a laptop compartment, and comfortable straps."),
            ("electronics", "سماعات أذن لاسلكية", "Wireless Earbuds", "wireless-earbuds", "NOVA-013", 19900, 26, "NOVA Audio", "حجم صغير وصوت واضح ومقاومة لرذاذ الماء.", "A compact fit, clear sound, and splash resistance."),
            ("computers", "جهاز لوحي 11 بوصة", "11-inch Tablet", "nova-tablet", "NOVA-014", 129900, 11, "Orbit", "شاشة واسعة للترفيه والدراسة مع بطارية طويلة.", "A spacious display for entertainment and study with long battery life."),
            ("home", "مصباح جانبي هادئ", "Ambient Table Lamp", "ambient-table-lamp", "NOVA-015", 14900, 23, "Luma", "إضاءة دافئة وتصميم بسيط يناسب غرفة النوم والمجلس.", "Warm lighting and a simple design for bedrooms and living spaces."),
            ("sports", "حذاء تدريب خفيف", "Lightweight Training Shoes", "training-shoes", "NOVA-016", 26900, 12, "Stride", "ثبات ومرونة للتمارين والنشاط اليومي.", "Stable and flexible support for workouts and daily activity."),
            ("travel", "حقيبة ظهر للسفر الخفيف", "Lightweight Travel Backpack", "travel-backpack", "NOVA-017", 22900, 5, "Nomad", "سعة عملية وتنظيم داخلي للرحلات القصيرة.", "Practical capacity and internal organization for short trips."),
            ("office", "لوحة مفاتيح مكتبية صغيرة", "Compact Office Keyboard", "compact-keyboard", "NOVA-018", 16900, 19, "KeyLab", "تصميم مدمج يوفر المساحة مع اتصال لاسلكي موثوق.", "A space-saving compact design with a reliable wireless connection."),
        ]
        seeded = {}
        for category_slug, name, name_en, slug, sku, price_cents, stock, brand, description, description_en in products:
            product, _ = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "category": categories[category_slug],
                    "name": name,
                    "name_en": name_en,
                    "slug": slug,
                    "price_cents": price_cents,
                    "stock": stock,
                    "low_stock_threshold": 8 if sku == "NOVA-006" else 5,
                    "reorder_quantity": 24,
                    "brand": brand,
                    "description": description,
                    "description_en": description_en,
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
                    "name_en": f"Size {size}",
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
