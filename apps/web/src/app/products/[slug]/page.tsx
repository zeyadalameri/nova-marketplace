"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage, formatMoney } from "@/lib/client-api";
import { localizedCategoryName, localizedProductDescription, localizedProductName, localizedVariantName } from "@/lib/i18n";
import type { Paginated, Product } from "@/lib/types";

type Review = { id: number; user_name: string; rating: number; title: string; comment: string; created_at: string };

export default function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>(); const router = useRouter();
  const { user, addToCart, toggleFavorite, favorites, currency, language } = useStore();
  const en = language === "en";
  const [product, setProduct] = useState<Product | null>(null); const [reviews, setReviews] = useState<Review[]>([]);
  const [variantId, setVariantId] = useState<number | null>(null); const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState(""); const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [item, reviewPayload] = await Promise.all([
        apiRequest<Product>(`/products/${slug}/?currency=${currency}`),
        apiRequest<Paginated<Review>>(`/reviews/?product=${slug}`),
      ]);
      setProduct(item); setReviews(reviewPayload.results); if (item.variants.length === 1) setVariantId(item.variants[0].id);
    } catch (error) { setMessage(errorMessage(error)); } finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [slug, currency]); // eslint-disable-line react-hooks/exhaustive-deps

  async function add() {
    if (!product) return;
    try { await addToCart(product, quantity, variantId); setMessage(en ? "Product added to your cart." : "أضيف المنتج إلى السلة."); }
    catch (error) { const text = errorMessage(error); setMessage(text); if (text.includes("سجّل الدخول")) router.push("/login"); }
  }
  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const formElement = event.currentTarget; const form = new FormData(formElement);
    try {
      await apiRequest("/reviews/", { method: "POST", body: JSON.stringify({ product_slug: slug, rating: Number(form.get("rating")), title: form.get("title"), comment: form.get("comment") }) });
      setMessage(en ? "Your review has been published." : "تم نشر تقييمك."); formElement.reset(); await load();
    } catch (error) { setMessage(errorMessage(error)); }
  }
  if (loading) return <main className="page container"><div className="loading">{en ? "Loading product…" : "جارٍ تحميل المنتج…"}</div></main>;
  if (!product) return <main className="page container"><div className="alert error">{message || (en ? "Product not found" : "المنتج غير موجود")}</div></main>;
  const selectedVariant = product.variants.find((variant) => variant.id === variantId);
  const price = selectedVariant?.display_price_cents ?? product.display_price_cents ?? product.price_cents;
  const image = product.images[0]?.url || product.image_url;
  const productName = localizedProductName(product, language);
  return <main className="page container"><div className="detail-grid"><div className="detail-image" style={image ? { backgroundImage: `url(${image})` } : undefined}>{!image && productName.slice(0,1)}</div><div className="detail-info"><p className="eyebrow">{localizedCategoryName(product.category, language)} · {product.brand}</p><h1>{productName}</h1><div>★ {product.average_rating} ({product.review_count} {en ? "reviews" : "تقييم"})</div><p className="detail-description">{localizedProductDescription(product, language)}</p><strong className="price-large">{formatMoney(price, product.currency, language === "ar" ? "ar-SA" : "en-US")}</strong>{product.variants.length > 0 && <><b>{en ? "Choose an option" : "اختر المواصفات"}</b><div className="variant-list">{product.variants.map((variant) => <button key={variant.id} className={variantId === variant.id ? "active" : ""} disabled={!variant.is_available} onClick={() => setVariantId(variant.id)}>{localizedVariantName(variant, language)} · {variant.stock} {en ? "available" : "متوفر"}</button>)}</div></>}<div className="field"><label htmlFor="quantity">{en ? "Quantity" : "الكمية"}</label><input id="quantity" type="number" min={1} max={selectedVariant?.stock ?? product.stock} value={quantity} onChange={(event) => setQuantity(Number(event.target.value))}/></div><div className="stack-actions"><button className="primary-button" disabled={!product.is_available || (product.has_variants && !variantId)} onClick={() => void add()}>{en ? "Add to cart" : "أضف للسلة"}</button><button className="secondary-button action-button" onClick={() => void toggleFavorite(product)}>{favorites.has(product.id) ? (en ? "Remove from favorites" : "إزالة من المفضلة") : (en ? "Add to favorites" : "أضف للمفضلة")}</button></div>{message && <div className="alert success">{message}</div>}</div></div><section className="reviews"><div className="section-title"><h2>{en ? "Customer reviews" : "تقييمات العملاء"}</h2><span>{reviews.length}</span></div>{user && <form className="panel" onSubmit={submitReview}><div className="form-grid"><div className="field"><label>{en ? "Rating" : "التقييم"}</label><select name="rating" defaultValue="5">{[5,4,3,2,1].map((rating) => <option value={rating} key={rating}>{rating} {en ? (rating === 1 ? "star" : "stars") : "نجوم"}</option>)}</select></div><div className="field"><label>{en ? "Title" : "العنوان"}</label><input name="title" /></div><div className="field full"><label>{en ? "Your comment" : "تعليقك"}</label><textarea name="comment" rows={3}/></div></div><button className="primary-button">{en ? "Publish review" : "نشر التقييم"}</button></form>}{reviews.map((review) => <article className="review" key={review.id}><h4>{review.user_name} · {"★".repeat(review.rating)}</h4><b>{review.title}</b><p>{review.comment}</p></article>)}</section></main>;
}
