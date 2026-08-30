"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";

export default function LoginPage() {
  const { login, language } = useStore();
  const en = language === "en";
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("username")), String(form.get("password")));
      router.push("/");
    } catch (err) { setError(err instanceof Error ? err.message : (en ? "Could not sign in" : "تعذر تسجيل الدخول")); }
    finally { setBusy(false); }
  }
  return <main className="page container"><form className="form-card" onSubmit={submit}><p className="eyebrow">{en ? "Welcome back" : "مرحبًا بعودتك"}</p><h1>{en ? "Sign in" : "تسجيل الدخول"}</h1>{error && <div className="alert error">{error}</div>}<div className="field"><label htmlFor="username">{en ? "Username or email" : "اسم المستخدم"}</label><input id="username" name="username" required autoComplete="username" /></div><div className="field"><label htmlFor="password">{en ? "Password" : "كلمة المرور"}</label><input id="password" name="password" type="password" required autoComplete="current-password" /></div><button disabled={busy}>{busy ? (en ? "Signing in…" : "جارٍ الدخول…") : (en ? "Sign in" : "دخول")}</button><p className="auth-switch">{en ? "New to NOVA?" : "ليس لديك حساب؟"} <Link href="/register">{en ? "Create an account" : "أنشئ حسابًا"}</Link></p></form></main>;
}
