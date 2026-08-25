"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage, formatMoney } from "@/lib/client-api";
import type { Paginated, Product } from "@/lib/types";

type Review = { id: number; user_name: string; rating: number; title: string; comment: string; created_at: string };

export default function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>(); const router = useRouter();
  const { user, addToCart, toggleFavorite, favorites, currency, language } = useStore();
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
    try { await addToCart(product, quantity, variantId); setMessage("أضيف المنتج إلى السلة."); }
    catch (error) { const text = errorMessage(error); setMessage(text); if (text.includes("سجّل الدخول")) router.push("/login"); }
  }
  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const formElement = event.currentTarget; const form = new FormData(formElement);
    try {
      await apiRequest("/reviews/", { method: "POST", body: JSON.stringify({ product_slug: slug, rating: Number(form.get("rating")), title: form.get("title"), comment: form.get("comment") }) });
      setMessage("تم نشر تقييمك."); formElement.reset(); await load();
    } catch (error) { setMessage(errorMessage(error)); }
  }
  if (loading) return <main className="page container"><div className="loading">جارٍ تحميل المنتج…</div></main>;
  if (!product) return <main className="page container"><div className="alert error">{message || "المنتج غير موجود"}</div></main>;
  const selectedVariant = product.variants.find((variant) => variant.id === variantId);
  const price = selectedVariant?.display_price_cents ?? product.display_price_cents ?? product.price_cents;
  const image = product.images[0]?.url || product.image_url;
  return <main className="page container"><div className="detail-grid"><div className="detail-image" style={image ? { backgroundImage: `url(${image})` } : undefined}>{!image && product.name.slice(0,1)}</div><div className="detail-info"><p className="eyebrow">{product.category.name} · {product.brand}</p><h1>{product.name}</h1><div>★ {product.average_rating} ({product.review_count} تقييم)</div><p className="detail-description">{product.description}</p><strong className="price-large">{formatMoney(price, product.currency, language === "ar" ? "ar-SA" : "en-US")}</strong>{product.variants.length > 0 && <><b>اختر المواصفات</b><div className="variant-list">{product.variants.map((variant) => <button key={variant.id} className={variantId === variant.id ? "active" : ""} disabled={!variant.is_available} onClick={() => setVariantId(variant.id)}>{variant.name} · {variant.stock} متوفر</button>)}</div></>}<div className="field"><label htmlFor="quantity">الكمية</label><input id="quantity" type="number" min={1} max={selectedVariant?.stock ?? product.stock} value={quantity} onChange={(event) => setQuantity(Number(event.target.value))}/></div><div className="stack-actions"><button className="primary-button" disabled={!product.is_available || (product.has_variants && !variantId)} onClick={() => void add()}>أضف للسلة</button><button className="secondary-button action-button" onClick={() => void toggleFavorite(product)}>{favorites.has(product.id) ? "إزالة من المفضلة" : "أضف للمفضلة"}</button></div>{message && <div className="alert success">{message}</div>}</div></div><section className="reviews"><div className="section-title"><h2>تقييمات العملاء</h2><span>{reviews.length}</span></div>{user && <form className="panel" onSubmit={submitReview}><div className="form-grid"><div className="field"><label>التقييم</label><select name="rating" defaultValue="5"><option value="5">5 نجوم</option><option value="4">4 نجوم</option><option value="3">3 نجوم</option><option value="2">نجمتان</option><option value="1">نجمة</option></select></div><div className="field"><label>العنوان</label><input name="title" /></div><div className="field full"><label>تعليقك</label><textarea name="comment" rows={3}/></div></div><button className="primary-button">نشر التقييم</button></form>}{reviews.map((review) => <article className="review" key={review.id}><h4>{review.user_name} · {"★".repeat(review.rating)}</h4><b>{review.title}</b><p>{review.comment}</p></article>)}</section></main>;
}
