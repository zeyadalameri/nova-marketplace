"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";

export default function LoginPage() {
  const { login } = useStore();
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("username")), String(form.get("password")));
      router.push("/");
    } catch (err) { setError(err instanceof Error ? err.message : "تعذر تسجيل الدخول"); }
    finally { setBusy(false); }
  }
  return <main className="page container"><form className="form-card" onSubmit={submit}><p className="eyebrow">مرحبًا بعودتك</p><h1>تسجيل الدخول</h1>{error && <div className="alert error">{error}</div>}<div className="field"><label htmlFor="username">اسم المستخدم</label><input id="username" name="username" required autoComplete="username" /></div><div className="field"><label htmlFor="password">كلمة المرور</label><input id="password" name="password" type="password" required autoComplete="current-password" /></div><button disabled={busy}>{busy ? "جارٍ الدخول…" : "دخول"}</button><p className="auth-switch">ليس لديك حساب؟ <Link href="/register">أنشئ حسابًا</Link></p></form></main>;
}
