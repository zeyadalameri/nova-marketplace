"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useStore } from "./StoreProvider";

const mainCategories = [
  ["electronics", "الإلكترونيات", "Electronics"],
  ["computers", "الكمبيوتر والألعاب", "Computers & Gaming"],
  ["home", "المنزل", "Home"],
  ["kitchen", "المطبخ", "Kitchen"],
  ["fashion", "الأزياء", "Fashion"],
  ["sports", "الرياضة", "Sports"],
  ["travel", "السفر", "Travel"],
  ["office", "المكتب والدراسة", "Office & Study"],
] as const;

export function StoreHeader() {
  const { user, cart, language, currency, t, setLanguage, setCurrency, logout } = useStore();
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
          <div><span>📍 {t("deliverTo")}</span><Link href="/orders">{t("trackOrder")}</Link><span>{t("helpCenter")}</span></div>
          <div><span>{t("freeShipping")}</span><button onClick={() => setLanguage(language === "ar" ? "en" : "ar")}>{language === "ar" ? "English" : "العربية"}</button></div>
        </div>
      </div>

      <div className="main-header">
        <div className="container header-main">
          <Link className="brand" href="/" aria-label={`NOVA ${t("home")}`}>
            <span>N</span><span className="brand-copy"><b>NOVA</b><small>MARKETPLACE</small></span>
          </Link>
          <form className="header-search" onSubmit={submitSearch} role="search">
            <select aria-label={t("searchDepartment")}><option>{t("allDepartments")}</option></select>
            <input aria-label={t("searchStore")} value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t("searchPlaceholder")} />
            <button type="submit" aria-label={t("submitSearch")}>⌕</button>
          </form>
          <div className="header-actions">
            <select className="currency-select" aria-label={t("currency")} value={currency} onChange={(event) => setCurrency(event.target.value as typeof currency)}><option value="SAR">SAR</option><option value="USD">USD</option><option value="AED">AED</option></select>
            <Link className="account-action" href={user ? "/account" : "/login"}><small>{user ? t("hello") : t("welcome")}</small><b>{user ? (user.first_name || user.username) : t("loginRegister")}</b></Link>
            <Link className="orders-action" href="/orders"><small>{t("orders")}</small><b>{t("trackShipment")}</b></Link>
            <Link className="cart-link" href="/cart" aria-label={t("cart")}><span>🛒</span><b>{cart?.item_count ?? 0}</b></Link>
          </div>
        </div>
      </div>

      <div className="header-nav">
        <div className="container nav-inner">
          <nav aria-label={t("mainNavigation")}>
            <Link className="nav-all" href="/#categories">☰ {t("allCategories")}</Link>
            {mainCategories.map(([slug, ar, en]) => <Link key={slug} href={`/categories/${slug}`}>{language === "ar" ? ar : en}</Link>)}
            <Link className="deals-nav" href="/#deals">{t("todayDeals")}</Link>
            {user?.is_staff && <Link className="ai-nav-link" href="/admin/ai-dashboard">✦ {t("aiDashboard")}</Link>}
          </nav>
          {user && <button className="logout-button" onClick={() => void logout()}>{t("logout")}</button>}
        </div>
      </div>
    </header>
  );
}
