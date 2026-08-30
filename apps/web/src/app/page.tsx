"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage } from "@/lib/client-api";
import { localizedCategoryDescription, localizedCategoryName } from "@/lib/i18n";
import type { Category, Paginated, Product } from "@/lib/types";

const categoryIcons: Record<string, string> = {
  electronics: "⌁", computers: "▣", home: "⌂", kitchen: "◉",
  fashion: "◇", sports: "◒", travel: "▤", office: "▦",
};

export default function Home() {
  const { currency, language, t } = useStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiRequest<Category[]>("/categories/").then(setCategories).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initial = params.get("q") ?? "";
    setQuery(initial);
    const handleSearch = (event: Event) => setQuery(String((event as CustomEvent).detail ?? ""));
    window.addEventListener("nova:search", handleSearch);
    return () => window.removeEventListener("nova:search", handleSearch);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams({ ordering: "newest", currency });
    if (query) params.set("q", query);
    setLoading(true);
    void apiRequest<Paginated<Product>>(`/products/?${params}`)
      .then((payload) => { setProducts(payload.results); setError(""); })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [currency, query]);

  const deals = useMemo(() => {
    const featured = products.filter((item) => item.is_featured);
    return (featured.length >= 5 ? featured : products).slice(0, 6);
  }, [products]);
  const recommendations = useMemo(() => products.filter((item) => !deals.some((deal) => deal.id === item.id)).slice(0, 8), [products, deals]);

  return (
    <main className="marketplace-home">
      {!query && <>
        <section className="market-hero">
          <div className="container market-hero-inner">
            <div className="hero-copy">
              <span className="hero-kicker">{t("launchOffers")}</span>
              <h1>{t("heroLineOne")}<br/><em>{t("heroLineTwo")}</em></h1>
              <p>{t("heroDescription")}</p>
              <div className="hero-actions"><a className="primary-button" href="#deals">{t("shopDeals")}</a><Link className="ghost-button" href="/categories/electronics">{t("discoverCategories")}</Link></div>
              <div className="hero-promo-line"><b>WELCOME10</b><span>{t("firstOrderDiscount")}</span></div>
            </div>
          </div>
        </section>

        <section className="benefits-bar container" aria-label={t("storeBenefits")}>
          <article><i>✓</i><div><b>{t("trustedProducts")}</b><small>{t("trustedProductsHint")}</small></div></article>
          <article><i>🚚</i><div><b>{t("fastDelivery")}</b><small>{t("fastDeliveryHint")}</small></div></article>
          <article><i>↺</i><div><b>{t("easyReturns")}</b><small>{t("easyReturnsHint")}</small></div></article>
          <article><i>▣</i><div><b>{t("securePayment")}</b><small>{t("securePaymentHint")}</small></div></article>
        </section>

        <section className="category-section container" id="categories">
          <div className="market-section-title"><div><span>{t("browseQuickly")}</span><h2>{t("shopByDepartment")}</h2></div><Link href="/categories/electronics">{t("viewAllCategories")}</Link></div>
          <div className="category-carousel">
            {categories.map((item) => <Link key={item.id} href={`/categories/${item.slug}`} className={`category-circle category-${item.slug}`}><i>{categoryIcons[item.slug] ?? "○"}</i><b>{localizedCategoryName(item, language)}</b><small>{localizedCategoryDescription(item, language)}</small></Link>)}
          </div>
        </section>
      </>}

      <section className="deal-section" id="deals">
        <div className="container">
          <div className="market-section-title"><div><span>{query ? t("searchResults") : t("selectedToday")}</span><h2>{query ? `${t("searchResults")}: “${query}”` : t("featuredProducts")}</h2></div><strong>{products.length} {t("product")}</strong></div>
          {error && <div className="store-error"><span>!</span><div><h3>{t("loadFailed")}</h3><p>{error} {t("backendHint")}</p></div></div>}
          {loading ? <ProductSkeletons label={t("loadingProducts")}/> : products.length ? <div className="deal-rail">{deals.map((product) => <ProductCard compact product={product} key={product.id}/>)}</div> : !error && <div className="empty-state"><h3>{t("noResults")}</h3><p>{t("tryAnotherSearch")}</p></div>}
        </div>
      </section>

      {!query && <>
        <section className="promo-grid container" aria-label={t("departmentOffers")}>
          <Link className="promo-tile promo-tech" href="/categories/electronics"><small>{t("techToday")}</small><h3>{t("smartDevices")}</h3><span>{t("shopNow")}</span><i>⌁</i></Link>
          <Link className="promo-tile promo-home" href="/categories/home"><small>{t("homePicks")}</small><h3>{t("smallDetails")}</h3><span>{t("discoverMore")}</span><i>⌂</i></Link>
          <Link className="promo-tile promo-fashion" href="/categories/fashion"><small>{t("justArrived")}</small><h3>{t("dailyEssentials")}</h3><span>{t("shopCollection")}</span><i>◇</i></Link>
        </section>

        <section className="wide-campaign container"><div><small>{t("weeklyOffer")}</small><h2>{t("prepareSmart")}</h2><p>{t("weeklyDescription")}</p><Link href="/categories/computers">{t("discoverCollection")}</Link></div><strong>{language === "ar" ? <>خصم<br/><b>حتى 25%</b></> : <>Save<br/><b>up to 25%</b></>}</strong></section>

        <section className="recommend-section container" id="catalog">
          <div className="market-section-title"><div><span>{t("mostPopular")}</span><h2>{t("youMayLike")}</h2></div><Link href="/categories/electronics">{t("viewAll")}</Link></div>
          {loading ? <ProductSkeletons label={t("loadingProducts")}/> : <div className="product-grid marketplace-product-grid">{(recommendations.length ? recommendations : products.slice(6, 14)).map((product) => <ProductCard product={product} key={product.id}/>)}</div>}
        </section>

        <section className="brand-strip container"><span>{t("selectedBrands")}</span>{["NOVA", "ORBIT", "LUMA", "STRIDE", "NOMAD", "KEYLAB"].map((brand) => <b key={brand}>{brand}</b>)}</section>
      </>}

      <StoreFooter />
    </main>
  );
}

function ProductSkeletons({ label }: { label: string }) {
  return <div className="deal-rail" aria-label={label}>{Array.from({ length: 5 }, (_, index) => <div className="product-skeleton" key={index}><i/><b/><span/><span/></div>)}</div>;
}

function StoreFooter() {
  const { language, t } = useStore();
  return <footer className="store-footer"><div className="container footer-grid"><div><Link className="footer-brand" href="/"><span>N</span><b>NOVA</b></Link><p>{t("footerDescription")}</p></div><div><b>{t("shop")}</b><Link href="/#categories">{t("allCategories")}</Link><Link href="/#deals">{t("todayDeals")}</Link><Link href="/favorites">{t("favorites")}</Link></div><div><b>{t("yourAccount")}</b><Link href="/account">{t("myAccount")}</Link><Link href="/orders">{t("orders")}</Link><Link href="/cart">{t("cart")}</Link></div><div><b>{t("customerService")}</b><p>{t("availableAllWeek")}</p><span>support@nova.local</span></div></div><div className="footer-bottom container">© 2026 NOVA Marketplace <span>{language === "ar" ? "العربية" : "English"} · SAR</span></div></footer>;
}
