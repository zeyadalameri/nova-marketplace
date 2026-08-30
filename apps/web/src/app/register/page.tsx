"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";

export default function RegisterPage() {
  const { register, language } = useStore(); const router = useRouter(); const en = language === "en";
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); const form = new FormData(event.currentTarget);
    try {
      await register(Object.fromEntries(["username","email","password","first_name","last_name","phone"].map((key) => [key, String(form.get(key) ?? "")])));
      router.push("/account");
    } catch (err) { setError(err instanceof Error ? err.message : (en ? "Could not create the account" : "تعذر إنشاء الحساب")); }
    finally { setBusy(false); }
  }
  return <main className="page container"><form className="form-card" onSubmit={submit}><p className="eyebrow">{en ? "Join NOVA" : "انضم إلى NOVA"}</p><h1>{en ? "Create an account" : "إنشاء حساب"}</h1>{error && <div className="alert error">{error}</div>}<div className="form-grid"><div className="field"><label htmlFor="first_name">{en ? "First name" : "الاسم الأول"}</label><input id="first_name" name="first_name" required /></div><div className="field"><label htmlFor="last_name">{en ? "Last name" : "اسم العائلة"}</label><input id="last_name" name="last_name" /></div><div className="field"><label htmlFor="username">{en ? "Username" : "اسم المستخدم"}</label><input id="username" name="username" required autoComplete="username" /></div><div className="field"><label htmlFor="phone">{en ? "Phone" : "الجوال"}</label><input id="phone" name="phone" inputMode="tel" /></div><div className="field full"><label htmlFor="email">{en ? "Email" : "البريد الإلكتروني"}</label><input id="email" name="email" type="email" required autoComplete="email" /></div><div className="field full"><label htmlFor="password">{en ? "Password" : "كلمة المرور"}</label><input id="password" name="password" type="password" minLength={8} required autoComplete="new-password" /></div></div><button disabled={busy}>{busy ? (en ? "Creating account…" : "جارٍ الإنشاء…") : (en ? "Create account" : "إنشاء الحساب")}</button><p className="auth-switch">{en ? "Already have an account?" : "لديك حساب؟"} <Link href="/login">{en ? "Sign in" : "سجّل الدخول"}</Link></p></form></main>;
}
