# معمارية NOVA Marketplace

## الصورة العامة

```text
Next.js Web ─────────┐
                     ├── HTTPS / JSON ── Django REST API ── PostgreSQL
Expo Android + iOS ──┘                         │
                                              ├── Object Storage / CDN
                                              ├── Payment + Webhooks
                                              ├── Shipping + Tracking
                                              ├── SMTP / Push
                                              ├── Inventory Monitor
                                              ├── Local Rules / OpenAI Analysis
                                              └── Sentry / Logs
```

الباك إند واحد للويب والجوال، لذلك توجد نسخة واحدة من قواعد الأسعار والكوبونات والضريبة والمخزون والطلبات. البنية الحالية Modular Monolith: أسهل في التطوير والنشر من الخدمات المصغرة، ويمكن فصل خدمة محددة لاحقًا عند وجود حمل مقاس يبرر ذلك.

## مسؤولية التقنيات

- **Next.js + TypeScript:** واجهة المتجر المتجاوبة، وصفحات المنتجات والشراء والحساب. توجد طبقة BFF داخل Next.js تحفظ JWT في Cookies من نوع HttpOnly ولا تعرضها لـ JavaScript في المتصفح.
- **Expo + React Native + TypeScript:** تطبيق واحد لـ Android وiOS، ويخزن JWT في SecureStore ويجدد Access Token تلقائيًا.
- **Django REST Framework:** المستخدمون والصلاحيات، الكتالوج، السلة، الأسعار، المخزون، الطلبات، الدفع، الشحن والإشعارات، مع لوحة Django Admin.
- **PostgreSQL:** قاعدة الإنتاج الموصى بها. SQLite مخصصة للتطوير المحلي السريع.

## وحدات الباك إند

- `accounts`: التسجيل، المستخدم، JWT والعناوين.
- `catalog`: التصنيفات والمنتجات والصور والمتغيرات والمفضلة والتقييمات.
- `carts`: السلة والعناصر والكوبون وعرض السعر.
- `orders`: Checkout والطلب والفاتورة والمخزون والإلغاء.
- `commerce`: العملات والكوبونات والدفع وWebhooks والشحن والإرجاع والإشعارات وأجهزة Push.
- `inventory`: الدُفعات والصلاحية وحركات المخزون والتنبيهات والتنبؤ بالنفاد وتقارير التحليل الذكي.
- `common`: Health Check واختبارات حدود الصلاحيات.

## أهم مسارات API

```text
GET    /api/v1/health/
GET    /api/v1/store/config/
POST   /api/v1/auth/register/
POST   /api/v1/auth/token/
POST   /api/v1/auth/token/refresh/
GET    /api/v1/auth/me/
GET    /api/v1/auth/addresses/
POST   /api/v1/auth/addresses/
GET    /api/v1/categories/
GET    /api/v1/products/?search=&category=&ordering=&currency=
GET    /api/v1/products/{slug}/
GET    /api/v1/reviews/
POST   /api/v1/reviews/
GET    /api/v1/favorites/
POST   /api/v1/favorites/
GET    /api/v1/cart/
POST   /api/v1/cart/items/
PATCH  /api/v1/cart/items/{id}/
POST   /api/v1/cart/coupon/
DELETE /api/v1/cart/coupon/
GET    /api/v1/orders/
POST   /api/v1/orders/
POST   /api/v1/orders/{id}/payment/
GET    /api/v1/orders/{id}/tracking/
POST   /api/v1/orders/{id}/cancel/
GET    /api/v1/payments/
POST   /api/v1/webhooks/payments/sandbox/
GET    /api/v1/shipments/
POST   /api/v1/returns/
GET    /api/v1/notifications/
POST   /api/v1/devices/
GET    /api/v1/admin/inventory/dashboard/
POST   /api/v1/admin/inventory/analyze/
POST   /api/v1/admin/inventory/adjust/
POST   /api/v1/admin/inventory/scan/
GET    /api/v1/admin/inventory/alerts/
GET    /api/v1/admin/inventory/movements/
```

Swagger الكامل متاح في `/api/docs/`. مسارات الحساب والسلة والمفضلة والطلبات والتجارة الخاصة تستخدم JWT وتطبق عزل بيانات كل مستخدم.

## سلامة الطلب والدفع

- يحسب الخادم الإجمالي ولا يثق بأسعار الواجهة.
- يغلق صفوف المخزون داخل Transaction عند إنشاء الطلب ثم يخصم الكمية.
- يخزن اسم المنتج والمتغير والسعر والعنوان والعملة داخل Snapshot للطلب.
- يستخدم `Idempotency-Key` في إنشاء الدفع، ويحفظ معرف حدث Webhook لمنع معالجته مرتين.
- يتحقق Webhook التجريبي من توقيع HMAC قبل تحديث الدفع والطلب.
- يعيد الإلغاء المخزون ويغيّر حالة الشحنة والدفع التجريبي عند الحاجة.
- يسجل البيع والإلغاء والتوريد والتسوية كسجل حركات غير صفري، ويستهلك الدُفعات الأقرب انتهاءً أولًا (FEFO).

## طبقة المخزون الذكية

- القواعد الحاسمة مثل منع المخزون السالب والتنبيه عند حد محدد تعمل داخل Django ولا تعتمد على نموذج لغوي.
- المراقب الدوري يكتشف النفاد والانخفاض وقرب/انتهاء الصلاحية والأصناف التي لم تتحرك خلال الفترة المحددة.
- التنبؤ بأيام النفاد يعتمد على معدل البيع الفعلي في الفترة المختارة، مع اقتراح توريد قابل للضبط لكل منتج أو متغير.
- المحلل المحلي يولد ملخصًا وتوصيات دون مفتاح. عند إعداد `OPENAI_API_KEY` يرسل الباك إند بيانات مخزون ومبيعات مجمعة فقط، دون أسماء أو عناوين أو هواتف العملاء، ويطلب نتيجة JSON منظمة.
- كل مسارات اللوحة محمية بصلاحية الموظف `is_staff`، وسجل تقارير التحليل محفوظ للمراجعة.

## حدود النسخة الحالية

واجهات مزودي الدفع والشحن الحالية Sandbox. التخزين المحلي والبريد إلى Console يعملان بدون حسابات خارجية، أما S3/CDN وSMTP وSentry وتسليم Push الفعلي فتحتاج مفاتيح مزودين. الضرائب الحالية نسبة قابلة للإعداد وليست محرك ضرائب متعدد الدول. واجهة اللغة تغيّر اتجاه وتجربة العرض، لكن ترجمة كتالوج ومحتوى قانوني كامل لكل سوق تحتاج بيانات وترجمات معتمدة.

## متطلبات إطلاق عالمي

- PostgreSQL مُدار مع نسخ احتياطي دوري واختبار استعادة.
- Reverse Proxy وTLS وWAF/CDN وسياسة أسرار منفصلة لكل بيئة.
- مزود دفع لا يمرر بيانات البطاقة إلى خوادم NOVA، مع Webhooks حقيقية.
- مزود شحن، SLA، عناوين معيارية، وسياسات إرجاع حسب الدولة.
- محرك ضرائب وفواتير متوافق مع السوق، وترجمة بشرية وسياسات خصوصية وشروط استخدام.
- Queue مثل Celery/Redis للبريد وPush والمهام الطويلة عند الانتقال من الحجم الصغير.
- CI/CD، مراقبة، تنبيهات، اختبارات أمن وتحميل مستمرة.
