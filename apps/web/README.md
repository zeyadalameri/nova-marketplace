# NOVA Web

واجهة المتجر العربية المبنية بـ Next.js وTypeScript.

```powershell
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

`API_URL` يستخدمه Next.js من جهة الخادم، و`NEXT_PUBLIC_API_URL` مخصص للطلبات التي ستعمل من المتصفح لاحقًا.
