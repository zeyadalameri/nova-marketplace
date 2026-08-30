"use client";

import Link from "next/link";
import { useState } from "react";

import { errorMessage, formatMoney } from "@/lib/client-api";
import { localizedCategoryName, localizedProductDescription, localizedProductName } from "@/lib/i18n";
import type { Product } from "@/lib/types";
import { ProductVisual } from "./ProductVisual";
import { useStore } from "./StoreProvider";

export function ProductCard({ product, compact = false }: { product: Product; compact?: boolean }) {
  const { addToCart, toggleFavorite, favorites, language, t } = useStore();
  const [message, setMessage] = useState("");
  const image = product.images[0]?.url || product.image_url;
  const price = product.display_price_cents ?? product.price_cents;
  const productName = localizedProductName(product, language);

  async function act(action: () => Promise<void>, success: string) {
    try { await action(); setMessage(success); } catch (error) { setMessage(errorMessage(error)); }
  }

  return (
    <article className={`product-card${compact ? " product-card-compact" : ""}`}>
      <div className="product-media">
        {product.is_featured && <span className="product-badge">{t("featuredOffer")}</span>}
        <button className="floating-favorite" aria-label={t("favorite")} onClick={() => void act(() => toggleFavorite(product), t("favoriteUpdated"))}>{favorites.has(product.id) ? "♥" : "♡"}</button>
        <Link href={`/products/${product.slug}`} aria-label={`${t("details")} ${productName}`}><ProductVisual name={productName} slug={product.slug} image={image}/></Link>
      </div>
      <div className="product-body">
        <div className="product-meta"><small>{localizedCategoryName(product.category, language)} · {product.brand}</small><span>★ {product.average_rating || t("new")}</span></div>
        <Link href={`/products/${product.slug}`}><h3>{productName}</h3></Link>
        <p className="product-description">{localizedProductDescription(product, language)}</p>
        <div className="product-bottom"><strong>{formatMoney(price, product.display_currency ?? product.currency, language === "ar" ? "ar-SA" : "en-US")}</strong><span className={product.is_available ? "in-stock" : "out-stock"}>{product.is_available ? t("inStock") : t("outOfStock")}</span></div>
        {product.is_available && <p className="delivery-note">{t("deliveryNote")}</p>}
        <div className="card-actions">
          <button disabled={!product.is_available || product.has_variants} onClick={() => void act(() => addToCart(product), t("addedToCart"))}>{product.has_variants ? t("chooseSize") : t("addToCart")}</button>
          <Link className="quick-view" href={`/products/${product.slug}`}>{t("details")}</Link>
        </div>
        {message && <p className="inline-message" role="status">{message}</p>}
      </div>
    </article>
  );
}
