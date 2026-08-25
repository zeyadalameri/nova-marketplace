# دليل اختبار NOVA Marketplace

## الفحوص الآلية

نفّذ الأوامر من جذر المشروع:

```powershell
.\venv\Scripts\python.exe apps\backend\manage.py test accounts carts catalog commerce orders inventory
.\venv\Scripts\python.exe apps\backend\manage.py check
.\venv\Scripts\python.exe apps\backend\manage.py spectacular --validate --file apps\backend\schema.yml
npm.cmd --prefix apps\web run lint
npm.cmd --prefix apps\web run build
Push-Location apps\mobile
npx.cmd tsc --noEmit
npx.cmd expo-doctor
npx.cmd expo export --platform android
npx.cmd expo export --platform ios
Pop-Location
npm.cmd --prefix apps\web audit --omit=dev --audit-level=high
npm.cmd --prefix apps\mobile audit --omit=dev --audit-level=high
.\venv\Scripts\python.exe -m pip install pip-audit
.\venv\Scripts\python.exe -m pip_audit -r apps\backend\requirements.txt
```

اختبارات Django تغطي التسجيل وJWT وعزل العناوين والبحث والمتغيرات والتقييمات والسلة والكوبون والضريبة وCheckout والمخزون والدفع وIdempotency وتوقيع Webhook والشحنة والإلغاء والإرجاع. كما تغطي صلاحيات لوحة المخزون، الدُفعات والصلاحية، تنبيهات الانخفاض وبطء الحركة، مسارات البيع والإلغاء، والتحليل المحلي عند غياب مفتاح OpenAI.

## اختبار لوحة المخزون الذكية

1. أنشئ مديرًا باستخدام `createsuperuser` وسجّل دخوله من الويب.
2. افتح `/admin/ai-dashboard` وتأكد من ظهور الأرصدة والتنبيهات والحركات.
3. أضف توريدًا برقم دفعة وتاريخ قريب، ثم تحقق من ظهور تنبيه الصلاحية.
4. اضغط **حلّل المخزون**؛ يجب أن يظهر `تحليل محلي` دون مفتاح أو `OpenAI` عند إعداد المفتاح.
5. شغّل `monitor_inventory --no-notifications` لفحص واحد، ثم جرّب وضع `--watch` في بيئة Staging.

فحص الويب الحالي يخرج دون ثغرات معروفة. يعرض `npm audit` في تطبيق الجوال أربعة تنبيهات عالية ناتجة عن `image-size` الذي تستخدمه أداة البناء Metro ضمن Expo 57. التنبيهان يتعلقان بتوقف أداة Node عند تحليل صور ICNS/JXL/HEIF مصممة بشكل خبيث، ولا توجد لهما نسخة مصححة منشورة حتى الآن. لا تعالج صورًا غير موثوقة داخل بيئة البناء، ولا تستخدم `npm audit fix --force` أو إصدار Expo تجريبيًا لمجرد إخفاء التنبيه؛ تابع تحديثات Expo/Metro ثم أعد التدقيق عند صدور إصلاح متوافق.

## اختبار رحلة شراء كاملة

شغّل الباك إند على المنفذ 8000 والويب على 3000، ثم:

1. أنشئ حسابًا جديدًا وتأكد أن إعادة تحميل الصفحة تبقي الجلسة.
2. أضف عنوانًا واجعله افتراضيًا.
3. افتح منتجًا، أضفه للمفضلة، وانشر تقييمًا.
4. أضف المنتج للسلة وغيّر الكمية عند الحاجة.
5. طبّق `WELCOME10` وتحقق من الخصم والضريبة والشحن والإجمالي.
6. انتقل إلى Checkout، اختر العنوان والدفع بالبطاقة، وأنشئ الطلب.
7. اضغط زر تأكيد الدفع التجريبي وتحقق من `paid` ورقم الفاتورة ورقم التتبع.
8. راجع قائمة الطلبات والإشعارات داخل الحساب.
9. لاختبار الإرجاع محليًا، غيّر طلب اختبار إلى `shipped` من لوحة الإدارة ثم أرسل سبب الإرجاع من صفحة الطلب.
10. اختبر العرض بعرض هاتف وتأكد من عدم وجود تمرير أفقي أو أخطاء Console.

## اختبار تحميل Smoke

مع تشغيل API:

```powershell
.\venv\Scripts\python.exe scripts\load_test.py --requests 100 --concurrency 10
```

السكربت يرسل طلبات متزامنة إلى قائمة المنتجات ويعيد عدد الإخفاقات والمتوسط وP95. هذا Smoke Test وليس بديلًا عن اختبار تحميل موزع بأرقام الإنتاج المتوقعة.

## فحوص Staging قبل الإطلاق

- إعادة رحلة الشراء باستخدام Sandbox الحقيقي لمزود الدفع ومزود الشحن.
- إعادة إرسال Webhook نفسه والتأكد أنه لا يكرر تحديث الطلب.
- اختبار بريد وPush وصور S3/CDN على حسابات Staging.
- اختبار الصلاحيات والحد من الطلبات وملفات كبيرة ومدخلات غير صحيحة.
- إنشاء نسخة PostgreSQL احتياطية، حذف بيانات في بيئة اختبار، ثم تجربة الاستعادة.
- فحص Android وiOS على أجهزة فعلية وشبكات بطيئة ومنقطعة.
- تنفيذ اختبار أمان وتحميل وفق SLA المتوقع قبل تفعيل عملاء حقيقيين.
