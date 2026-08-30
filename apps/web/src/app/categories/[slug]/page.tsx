"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage } from "@/lib/client-api";
import { localizedCategoryDescription, localizedCategoryName } from "@/lib/i18n";
import type { Category, Paginated, Product } from "@/lib/types";

export default function CategoryPage() {
  const { slug } = useParams<{ slug: string }>();
  const { currency, language, t } = useStore();
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
      <div className="category-crumb container"><Link href="/">{t("home")}</Link><span>›</span><span>{localizedCategoryName(category, language)}</span></div>
      <section className={`category-hero category-hero-${slug}`}><div className="container"><div><small>{t("novaDepartment")}</small><h1>{category ? localizedCategoryName(category, language) : t("shopByDepartment")}</h1><p>{localizedCategoryDescription(category, language)}</p></div><i>{categorySymbol(slug)}</i></div></section>

      <div className="container category-layout">
        <aside className="category-sidebar">
          <h2>{t("filterResults")}</h2>
          <section><h3>{t("categories")}</h3><nav>{categories.map((item) => <Link className={item.slug === slug ? "active" : ""} href={`/categories/${item.slug}`} key={item.id}>{localizedCategoryName(item, language)}<span>‹</span></Link>)}</nav></section>
          <section><h3>{t("price")}</h3>{[["", t("allPrices")], ["under-300", t("under300")], ["300-1000", t("between300And1000")], ["over-1000", t("over1000")]].map(([value, label]) => <label key={value}><input type="radio" name="price" checked={price === value} onChange={() => setPrice(value)}/>{label}</label>)}</section>
          <section><h3>{t("availability")}</h3><label><input type="checkbox" checked={available} onChange={(event) => setAvailable(event.target.checked)}/>{t("availableOnly")}</label></section>
          {!!brands.length && <section><h3>{t("brands")}</h3>{brands.map((brand) => <label key={brand}><input type="checkbox" disabled/>{brand}</label>)}</section>}
        </aside>

        <section className="category-results">
          <div className="results-toolbar"><div><h2>{localizedCategoryName(category, language)}</h2><small>{products.length} {t("availableProducts")}</small></div><label>{t("sortBy")} <select value={ordering} onChange={(event) => setOrdering(event.target.value)}><option value="newest">{t("newest")}</option><option value="price">{t("priceLow")}</option><option value="-price">{t("priceHigh")}</option></select></label></div>
          <form className="category-search" onSubmit={submit}><input aria-label={t("searchStore")} value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`${t("search")} — ${localizedCategoryName(category, language)}`}/><button>{t("search")}</button></form>
          {error && <div className="store-error"><span>!</span><div><h3>{t("productLoadFailed")}</h3><p>{error}</p></div></div>}
          {loading ? <div className="category-loading">{t("loading")}</div> : products.length ? <div className="product-grid category-product-grid">{products.map((product) => <ProductCard product={product} key={product.id}/>)}</div> : !error && <div className="empty-state"><h3>{t("noMatchingProducts")}</h3><p>{t("adjustFilters")}</p></div>}
        </section>
      </div>
    </main>
  );
}

function categorySymbol(slug: string) {
  return ({ electronics: "⌁", computers: "▣", home: "⌂", kitchen: "◉", fashion: "◇", sports: "◒", travel: "▤", office: "▦" } as Record<string, string>)[slug] ?? "○";
}
