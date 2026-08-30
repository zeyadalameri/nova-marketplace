# NOVA Mobile

تطبيق Expo وReact Native من قاعدة TypeScript واحدة لأندرويد وiOS.

## Android Studio على Windows

من جذر المشروع يمكن تشغيل البيئة كاملة بملف واحد:

```cmd
start_android.cmd
```

يستخدم التشغيل المحلي JDK 17 وAndroid API 36 ومحاكي `NOVA_API_36`. عنوان Django داخل Android Emulator هو `http://10.0.2.2:8000/api/v1`. مجلد `android` مولّد بواسطة Expo؛ إذا لم يكن موجودًا ينشئه ملف التشغيل قبل فتحه في Android Studio.

للتشغيل اليدوي:

```powershell
Set-Location apps\mobile
npm.cmd install
npx.cmd expo prebuild --platform android
npx.cmd expo run:android
```

```powershell
Copy-Item .env.example .env
npm.cmd install
npm.cmd start
```

على هاتف حقيقي، غيّر `EXPO_PUBLIC_API_URL` إلى عنوان IP المحلي للكمبيوتر الذي يشغّل Django.
