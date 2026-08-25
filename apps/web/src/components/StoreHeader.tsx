"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useStore } from "./StoreProvider";

const mainCategories = [
  ["electronics", "الإلكترونيات"],
  ["computers", "الكمبيوتر والألعاب"],
  ["home", "المنزل"],
  ["kitchen", "المطبخ"],
  ["fashion", "الأزياء"],
  ["sports", "الرياضة"],
  ["travel", "السفر"],
  ["office", "المكتب والدراسة"],
] as const;

export function StoreHeader() {
  const { user, cart, language, currency, setLanguage, setCurrency, logout } = useStore();
  const [search, setSearch] = useState("");

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    const value = search.trim();
    if (window.location.pathname === "/") {
      window.dispatchEvent(new CustomEvent("nova:search", { detail: value }));
      window.location.hash = "catalog";
    } else {
      window.location.assign(`/?q=${encodeURIComponent(value)}#catalog`);
    }
  }

  return (
    <header className="store-header">
      <div className="utility-bar">
        <div className="container utility-inner">
          <div><span>📍 التوصيل إلى الرياض</span><Link href="/orders">تتبّع طلبك</Link><span>مركز المساعدة</span></div>
          <div><span>شحن مجاني فوق 300 ر.س</span><button onClick={() => setLanguage(language === "ar" ? "en" : "ar")}>{language === "ar" ? "English" : "العربية"}</button></div>
        </div>
      </div>

      <div className="main-header">
        <div className="container header-main">
          <Link className="brand" href="/" aria-label="NOVA الرئيسية">
            <span>N</span><span className="brand-copy"><b>NOVA</b><small>MARKETPLACE</small></span>
          </Link>
          <form className="header-search" onSubmit={submitSearch} role="search">
            <select aria-label="قسم البحث"><option>كل الأقسام</option></select>
            <input aria-label="ابحث في المتجر" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ابحث عن منتج أو علامة تجارية أو قسم" />
            <button type="submit" aria-label="تنفيذ البحث">⌕</button>
          </form>
          <div className="header-actions">
            <select className="currency-select" aria-label="العملة" value={currency} onChange={(event) => setCurrency(event.target.value as typeof currency)}><option value="SAR">SAR</option><option value="USD">USD</option><option value="AED">AED</option></select>
            <Link className="account-action" href={user ? "/account" : "/login"}><small>{user ? "مرحبًا" : "أهلًا بك"}</small><b>{user ? (user.first_name || user.username) : "دخول / تسجيل"}</b></Link>
            <Link className="orders-action" href="/orders"><small>الطلبات</small><b>تتبّع الشحنة</b></Link>
            <Link className="cart-link" href="/cart" aria-label="سلة التسوق"><span>🛒</span><b>{cart?.item_count ?? 0}</b></Link>
          </div>
        </div>
      </div>

      <div className="header-nav">
        <div className="container nav-inner">
          <nav aria-label="التنقل الرئيسي">
            <Link className="nav-all" href="/#categories">☰ جميع الأقسام</Link>
            {mainCategories.map(([slug, label]) => <Link key={slug} href={`/categories/${slug}`}>{label}</Link>)}
            <Link className="deals-nav" href="/#deals">عروض اليوم</Link>
            {user?.is_staff && <Link className="ai-nav-link" href="/admin/ai-dashboard">✦ لوحة الذكاء</Link>}
          </nav>
          {user && <button className="logout-button" onClick={() => void logout()}>خروج</button>}
        </div>
      </div>
    </header>
  );
}
