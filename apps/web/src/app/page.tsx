"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage } from "@/lib/client-api";
import type { Category, Paginated, Product } from "@/lib/types";

const categoryIcons: Record<string, string> = {
  electronics: "⌁", computers: "▣", home: "⌂", kitchen: "◉",
  fashion: "◇", sports: "◒", travel: "▤", office: "▦",
};

export default function Home() {
  const { currency } = useStore();
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
              <span className="hero-kicker">عروض إطلاق NOVA</span>
              <h1>كل احتياجاتك<br/><em>في مكان واحد</em></h1>
              <p>إلكترونيات، منزل، أزياء وسفر بتجربة عربية سريعة وآمنة.</p>
              <div className="hero-actions"><a className="primary-button" href="#deals">تسوّق العروض</a><Link className="ghost-button" href="/categories/electronics">اكتشف الأقسام</Link></div>
              <div className="hero-promo-line"><b>WELCOME10</b><span>خصم 10% على أول طلب</span></div>
            </div>
          </div>
        </section>

        <section className="benefits-bar container" aria-label="مزايا المتجر">
          <article><i>✓</i><div><b>منتجات موثوقة</b><small>اختيارات بجودة مضمونة</small></div></article>
          <article><i>🚚</i><div><b>توصيل سريع</b><small>متابعة مباشرة للطلب</small></div></article>
          <article><i>↺</i><div><b>إرجاع سهل</b><small>خلال 14 يومًا</small></div></article>
          <article><i>▣</i><div><b>دفع آمن</b><small>حماية كاملة لبياناتك</small></div></article>
        </section>

        <section className="category-section container" id="categories">
          <div className="market-section-title"><div><span>تصفّح بسرعة</span><h2>تسوّق حسب القسم</h2></div><Link href="/categories/electronics">عرض جميع الأقسام ←</Link></div>
          <div className="category-carousel">
            {categories.map((item) => <Link key={item.id} href={`/categories/${item.slug}`} className={`category-circle category-${item.slug}`}><i>{categoryIcons[item.slug] ?? "○"}</i><b>{item.name}</b><small>{item.description}</small></Link>)}
          </div>
        </section>

        <section className="promo-grid container" aria-label="عروض الأقسام">
          <Link className="promo-tile promo-tech" href="/categories/electronics"><small>تقنية اليوم</small><h3>أجهزة ذكية<br/>لحياة أسهل</h3><span>تسوّق الآن ←</span><i>⌁</i></Link>
          <Link className="promo-tile promo-home" href="/categories/home"><small>اختيارات المنزل</small><h3>تفاصيل صغيرة<br/>تصنع فرقًا</h3><span>اكتشف المزيد ←</span><i>⌂</i></Link>
          <Link className="promo-tile promo-fashion" href="/categories/fashion"><small>وصل حديثًا</small><h3>أساسيات يومية<br/>بأسلوبك</h3><span>تسوّق المجموعة ←</span><i>◇</i></Link>
        </section>
      </>}

      <section className="deal-section" id="deals">
        <div className="container">
          <div className="market-section-title"><div><span>{query ? "نتائج البحث" : "مختارة لك اليوم"}</span><h2>{query ? `نتائج “${query}”` : "عروض ومنتجات مميزة"}</h2></div><strong>{products.length} منتج</strong></div>
          {error && <div className="store-error"><span>!</span><div><h3>تعذر تحميل البيانات</h3><p>{error} شغّل خادم Django على المنفذ 8000 ثم حدّث الصفحة.</p></div></div>}
          {loading ? <ProductSkeletons/> : products.length ? <div className="deal-rail">{deals.map((product) => <ProductCard compact product={product} key={product.id}/>)}</div> : !error && <div className="empty-state"><h3>لا توجد نتائج</h3><p>جرّب عبارة بحث مختلفة.</p></div>}
        </div>
      </section>

      {!query && <>
        <section className="wide-campaign container"><div><small>عرض الأسبوع</small><h2>جهّز يومك بذكاء</h2><p>منتجات للعمل والمنزل والسفر، مختارة لتمنحك قيمة أفضل.</p><Link href="/categories/computers">اكتشف المجموعة</Link></div><strong>خصم<br/><b>حتى 25%</b></strong></section>

        <section className="recommend-section container" id="catalog">
          <div className="market-section-title"><div><span>الأكثر طلبًا</span><h2>قد يعجبك أيضًا</h2></div><Link href="/categories/electronics">مشاهدة الكل ←</Link></div>
          {loading ? <ProductSkeletons/> : <div className="product-grid marketplace-product-grid">{(recommendations.length ? recommendations : products.slice(6, 14)).map((product) => <ProductCard product={product} key={product.id}/>)}</div>}
        </section>

        <section className="brand-strip container"><span>علامات مختارة</span>{["NOVA", "ORBIT", "LUMA", "STRIDE", "NOMAD", "KEYLAB"].map((brand) => <b key={brand}>{brand}</b>)}</section>
      </>}

      <StoreFooter />
    </main>
  );
}

function ProductSkeletons() {
  return <div className="deal-rail" aria-label="جارٍ تحميل المنتجات">{Array.from({ length: 5 }, (_, index) => <div className="product-skeleton" key={index}><i/><b/><span/><span/></div>)}</div>;
}

function StoreFooter() {
  return <footer className="store-footer"><div className="container footer-grid"><div><Link className="footer-brand" href="/"><span>N</span><b>NOVA</b></Link><p>سوق عربي موحد للويب والهاتف، يجمع تجربة التسوق والإدارة الذكية في مكان واحد.</p></div><div><b>تسوّق</b><Link href="/#categories">كل الأقسام</Link><Link href="/#deals">عروض اليوم</Link><Link href="/favorites">المفضلة</Link></div><div><b>حسابك</b><Link href="/account">حسابي</Link><Link href="/orders">الطلبات</Link><Link href="/cart">السلة</Link></div><div><b>خدمة العملاء</b><p>متاحون طوال أيام الأسبوع</p><span>support@nova.local</span></div></div><div className="footer-bottom container">© 2026 NOVA Marketplace <span>العربية · SAR</span></div></footer>;
}
