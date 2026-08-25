"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage } from "@/lib/client-api";
import type { Category, Paginated, Product } from "@/lib/types";

export default function CategoryPage() {
  const { slug } = useParams<{ slug: string }>();
  const { currency } = useStore();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [ordering, setOrdering] = useState("newest");
  const [price, setPrice] = useState("");
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { void apiRequest<Category[]>("/categories/").then(setCategories).catch(() => setCategories([])); }, []);
  useEffect(() => {
    const params = new URLSearchParams({ category: slug, ordering, currency });
    if (appliedQuery) params.set("q", appliedQuery);
    if (available) params.set("available", "true");
    if (price === "under-300") params.set("max_price", "30000");
    if (price === "300-1000") { params.set("min_price", "30000"); params.set("max_price", "100000"); }
    if (price === "over-1000") params.set("min_price", "100000");
    setLoading(true);
    void apiRequest<Paginated<Product>>(`/products/?${params}`)
      .then((payload) => { setProducts(payload.results); setError(""); })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [slug, ordering, currency, appliedQuery, price, available]);

  const category = useMemo(() => categories.find((item) => item.slug === slug), [categories, slug]);
  const brands = useMemo(() => Array.from(new Set(products.map((item) => item.brand).filter(Boolean))).slice(0, 8), [products]);

  function submit(event: FormEvent) { event.preventDefault(); setAppliedQuery(query.trim()); }

  return (
    <main className="category-page">
      <div className="category-crumb container"><Link href="/">الرئيسية</Link><span>›</span><span>{category?.name ?? "القسم"}</span></div>
      <section className={`category-hero category-hero-${slug}`}><div className="container"><div><small>قسم NOVA</small><h1>{category?.name ?? "تسوّق حسب القسم"}</h1><p>{category?.description ?? "اكتشف مجموعة مختارة من المنتجات والعروض."}</p></div><i>{categorySymbol(slug)}</i></div></section>

      <div className="container category-layout">
        <aside className="category-sidebar">
          <h2>تصفية النتائج</h2>
          <section><h3>الأقسام</h3><nav>{categories.map((item) => <Link className={item.slug === slug ? "active" : ""} href={`/categories/${item.slug}`} key={item.id}>{item.name}<span>‹</span></Link>)}</nav></section>
          <section><h3>السعر</h3>{[["", "كل الأسعار"], ["under-300", "أقل من 300 ر.س"], ["300-1000", "300 – 1,000 ر.س"], ["over-1000", "أكثر من 1,000 ر.س"]].map(([value, label]) => <label key={value}><input type="radio" name="price" checked={price === value} onChange={() => setPrice(value)}/>{label}</label>)}</section>
          <section><h3>التوفر</h3><label><input type="checkbox" checked={available} onChange={(event) => setAvailable(event.target.checked)}/>المتوفر فقط</label></section>
          {!!brands.length && <section><h3>العلامات</h3>{brands.map((brand) => <label key={brand}><input type="checkbox" disabled/>{brand}</label>)}</section>}
        </aside>

        <section className="category-results">
          <div className="results-toolbar"><div><h2>{category?.name}</h2><small>{products.length} منتج متاح</small></div><label>ترتيب حسب <select value={ordering} onChange={(event) => setOrdering(event.target.value)}><option value="newest">الأحدث</option><option value="price">السعر: الأقل أولًا</option><option value="-price">السعر: الأعلى أولًا</option></select></label></div>
          <form className="category-search" onSubmit={submit}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`ابحث داخل ${category?.name ?? "القسم"}`}/><button>بحث</button></form>
          {error && <div className="store-error"><span>!</span><div><h3>تعذر تحميل المنتجات</h3><p>{error}</p></div></div>}
          {loading ? <div className="category-loading">جارٍ تحميل المنتجات…</div> : products.length ? <div className="product-grid category-product-grid">{products.map((product) => <ProductCard product={product} key={product.id}/>)}</div> : !error && <div className="empty-state"><h3>لا توجد منتجات مطابقة</h3><p>أزل بعض الفلاتر أو ابحث بكلمة أخرى.</p></div>}
        </section>
      </div>
    </main>
  );
}

function categorySymbol(slug: string) {
  return ({ electronics: "⌁", computers: "▣", home: "⌂", kitchen: "◉", fashion: "◇", sports: "◒", travel: "▤", office: "▦" } as Record<string, string>)[slug] ?? "○";
}
