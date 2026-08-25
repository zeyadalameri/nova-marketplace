# NOVA Marketplace

منصة تجارة إلكترونية عربية بباك إند واحد يخدم الويب وتطبيق Android وiOS:

- الويب: Next.js + TypeScript.
- الجوال: Expo + React Native + TypeScript.
- الباك إند: Django REST Framework + JWT.
- قاعدة البيانات: SQLite للتطوير المحلي وPostgreSQL للإنتاج.

تم حذف مشروع Flask القديم بالكامل. المشروع الحالي يعتمد فقط على Django وNext.js وExpo.

## ما يعمل الآن

- التسجيل والدخول وتجديد الجلسة؛ الويب يستخدم Cookies من نوع HttpOnly والجوال يحفظ الرموز في SecureStore.
- التصنيفات والبحث والترتيب وتفاصيل المنتجات والصور والمتغيرات مثل الحجم واللون.
- المفضلة والتقييمات والمراجعات.
- سلة موحدة، كميات، كوبونات، ضريبة وشحن وحساب إجمالي موثوق في الخادم.
- عناوين متعددة وCheckout وطلبات وفواتير وتتبع وإلغاء وإرجاع.
- دفع وشحن تجريبيان محليان، Webhook موقّع، ومفاتيح Idempotency لمنع التكرار.
- عملات SAR وUSD وAED مع تثبيت عملة وقيمة الطلب وقت الشراء.
- إشعارات داخل التطبيق، تسجيل أجهزة Push، وبريد عبر Console أو SMTP.
- رفع صور محليًا أو إلى S3/خدمة متوافقة وربطها بـ CDN من خلال إعداد المزود.
- تحديد معدل API، إعدادات أمان للإنتاج، Sentry اختياري، Health Check ونسخ احتياطي واختبار تحميل.
- لوحة موظفين ذكية للمخزون تعرض حركة الوارد والمبيعات، وتتنبأ بأيام النفاد، وتقترح كمية إعادة الطلب.
- إدارة الدُفعات وتواريخ الصلاحية، وتنبيهات للنفاد والمخزون المنخفض وقرب الانتهاء والأصناف بطيئة الحركة.
- محلل عربي يعمل بقواعد محلية دون خدمات خارجية، ويمكن ربطه اختياريًا بـ OpenAI لتحليل أعمق؛ لا تُرسل إليه بيانات العملاء.

هذه نسخة MVP متكاملة وقابلة للتشغيل والاختبار. الإطلاق التجاري الحقيقي يحتاج مفاتيح واختيار مزودي الدفع والشحن والبريد والتخزين وPush، وسياسات الضرائب والفواتير لكل دولة؛ المحولات الحالية لهذه الخدمات محلية/تجريبية وليست عقودًا مع شركات فعلية.

## قاعدة البيانات المناسبة

التطوير المحلي يستخدم:

```text
apps/backend/db.sqlite3
```

للإنتاج استخدم PostgreSQL؛ وهو الاختيار الموصى به للمعاملات والمخزون والطلبات والفهارس والنسخ الاحتياطي. يمكن تشغيل MySQL بعد إضافة مشغله وتغيير `DATABASE_URL`. ويمكن استخدام SQL Server بواسطة `mssql-django` وMicrosoft ODBC Driver، لكنه يحتاج إعدادًا واختبارات خاصة، ولا يقدم فائدة واضحة لهذا المشروع مقارنة بـ PostgreSQL.

## التشغيل المحلي

### 1. الباك إند

من جذر المشروع في PowerShell:

```powershell
.\venv\Scripts\python.exe -m pip install -r apps\backend\requirements.txt
.\venv\Scripts\python.exe apps\backend\manage.py migrate
.\venv\Scripts\python.exe apps\backend\manage.py seed_demo
.\venv\Scripts\python.exe apps\backend\manage.py runserver 0.0.0.0:8000
```

- API: `http://127.0.0.1:8000/api/v1/`
- Swagger: `http://127.0.0.1:8000/api/docs/`
- لوحة الإدارة: `http://127.0.0.1:8000/admin/`

لإنشاء مدير:

```powershell
.\venv\Scripts\python.exe apps\backend\manage.py createsuperuser
```

بعد الدخول بحساب المدير من واجهة المتجر افتح:

```text
http://127.0.0.1:3000/admin/ai-dashboard
```

ولتفعيل المراقبة المستمرة محليًا افتح نافذة رابعة وشغّل:

```powershell
.\venv\Scripts\python.exe apps\backend\manage.py monitor_inventory --watch --interval 300
```

المراقب يفحص كل خمس دقائق ويرسل التنبيه داخل النظام وإلى بريد الموظفين إذا كان SMTP مفعّلًا. في Docker تعمل خدمة `inventory_monitor` تلقائيًا.

### تفعيل محلل OpenAI الاختياري

ضع المفتاح في بيئة الباك إند فقط، ولا تضعه في Next.js أو Expo:

```powershell
$env:OPENAI_API_KEY="ضع-المفتاح-هنا"
$env:OPENAI_INVENTORY_MODEL="gpt-5.6-terra"
```

ثم أعد تشغيل الباك إند. عند عدم وجود المفتاح تستمر اللوحة والتحذيرات والتوقعات في العمل بالمحلل المحلي الآمن، وتوضح الواجهة مصدر كل تحليل.

### 2. الويب

في نافذة PowerShell ثانية:

```powershell
Set-Location apps\web
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

افتح `http://127.0.0.1:3000`، وأنشئ حسابًا جديدًا. رمز الخصم التجريبي هو `WELCOME10`، والدفع بالبطاقة يعرض زرًا محليًا لمحاكاة Webhook الناجح.

### 3. تطبيق Android وiOS

في نافذة PowerShell ثالثة:

```powershell
Set-Location apps\mobile
Copy-Item .env.example .env
npm.cmd install
npm.cmd start
```

- Android Emulator يصل إلى جهازك غالبًا عبر `10.0.2.2:8000`.
- iOS Simulator على جهاز Mac يصل عبر `127.0.0.1:8000`؛ لا يتوفر iOS Simulator محليًا على Windows.
- الهاتف الحقيقي يحتاج IP الكمبيوتر داخل `apps/mobile/.env`، مثل:

```dotenv
EXPO_PUBLIC_API_URL=http://192.168.1.20:8000/api/v1
```

يجب أن يكون الهاتف والكمبيوتر على الشبكة نفسها وأن يسمح جدار الحماية بالاتصال.

المشروع يستخدم Expo Development Build لأنه الأنسب للمشروع الإنتاجي ويدعم الوحدات الأصلية. على Windows مع Android Studio:

```powershell
Set-Location apps\mobile
npx.cmd expo run:android
```

لجهاز Android موصول عبر USB أضف `--device`. أما بناء iPhone من Windows فيتم عبر EAS السحابي (يتطلب حساب Expo، ولتثبيت Development Build على iPhone يلزم حساب Apple Developer):

```powershell
npm.cmd install --global eas-cli
eas.cmd login
eas.cmd build --platform ios --profile development
npx.cmd expo start --dev-client
```

ملف إعداد EAS موجود في `apps/mobile/eas.json`. ويمكن استخدام `--platform android` بدل `ios` لبناء Android سحابيًا أيضًا.

## الاختبارات

```powershell
.\venv\Scripts\python.exe apps\backend\manage.py test accounts carts catalog commerce orders inventory
.\venv\Scripts\python.exe apps\backend\manage.py spectacular --validate --file apps\backend\schema.yml
npm.cmd --prefix apps\web run lint
npm.cmd --prefix apps\web run build
Push-Location apps\mobile
npx.cmd tsc --noEmit
npx.cmd expo-doctor
npx.cmd expo export --platform android
npx.cmd expo export --platform ios
Pop-Location
.\venv\Scripts\python.exe scripts\load_test.py --requests 100 --concurrency 10
```

## تشغيل PostgreSQL ونسخة الإنتاج بالحاويات

يتطلب Docker Desktop وخادم HTTPS/Reverse Proxy قبل فتحه للإنترنت:

```powershell
Copy-Item .env.production.example .env
# عدّل كلمات المرور والأسرار والنطاقات والمزودين داخل .env
docker compose up --build
```

لا تستخدم القيم الافتراضية للأسرار في الإنتاج. لتصدير نسخة PostgreSQL احتياطية:

```powershell
.\scripts\backup-postgres.ps1
```

يمكن تمرير `-Database` و`-Username` إذا غيّرت اسمي قاعدة البيانات والمستخدم.

## الخدمات الخارجية قبل الإطلاق

- استبدال `sandbox` في الدفع بمزود فعلي وتنفيذ Adapter الخاص به مع مفاتيح Webhook.
- استبدال شحن `sandbox` بواجهة شركة الشحن وأسعارها وحالاتها.
- إدخال إعدادات S3/CDN وSMTP وSentry في `.env`.
- ربط مزود Push فعلي؛ تسجيل الأجهزة والإشعارات الداخلية موجودان، لكن التسليم الخارجي يحتاج المزود ومفاتيحه.
- اعتماد قواعد ضريبة وفاتورة وإرجاع وخصوصية خاصة بكل دولة مستهدفة.
- إعداد Reverse Proxy وTLS وCI/CD وجدول نسخ احتياطي مع اختبار الاستعادة.

راجع [المعمارية](docs/ARCHITECTURE.md) و[خارطة التنفيذ](docs/ROADMAP.md) و[دليل الاختبار](docs/TESTING.md) للتفاصيل.
