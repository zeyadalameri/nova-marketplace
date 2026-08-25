"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useStore } from "@/components/StoreProvider";
import { errorMessage, formatMoney } from "@/lib/client-api";

export default function CartPage() {
  const { user, cart, updateCartItem, removeCartItem, applyCoupon, removeCoupon, language } = useStore();
  const [message, setMessage] = useState("");
  async function coupon(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const code = String(new FormData(event.currentTarget).get("code")); try { await applyCoupon(code); setMessage("تم تطبيق رمز الخصم."); } catch (error) { setMessage(errorMessage(error)); } }
  if (!user) return <main className="page container"><div className="empty-state"><h1>سجّل الدخول لعرض سلتك</h1><Link className="primary-button" href="/login">تسجيل الدخول</Link></div></main>;
  if (!cart?.items.length) return <main className="page container"><div className="empty-state"><h1>سلتك فارغة</h1><p>أضف منتجاتك المفضلة ثم عد إلى هنا.</p><Link className="primary-button" href="/">متابعة التسوق</Link></div></main>;
  const money = (value: number) => formatMoney(value, cart.currency, language === "ar" ? "ar-SA" : "en-US");
  return <main className="page container"><div className="page-heading"><p className="eyebrow">راجع مشترياتك</p><h1>سلة التسوق</h1></div>{message && <div className={message.includes("تم") ? "alert success" : "alert error"}>{message}</div>}<div className="cart-layout"><section className="panel">{cart.items.map((item) => { const image = item.product.images[0]?.url || item.product.image_url; return <article className="cart-item" key={item.id}><div className="cart-thumb" style={image ? { backgroundImage: `url(${image})` } : undefined}>{!image && item.product.name.slice(0,1)}</div><div><Link href={`/products/${item.product.slug}`}><h3>{item.product.name}</h3></Link><p>{item.variant?.name}</p><strong>{money(item.line_total_cents)}</strong></div><div><div className="quantity-control"><button aria-label="تقليل" disabled={item.quantity <= 1} onClick={() => void updateCartItem(item.id, item.quantity - 1)}>−</button><b>{item.quantity}</b><button aria-label="زيادة" onClick={() => void updateCartItem(item.id, item.quantity + 1)}>+</button></div><button className="danger-button" onClick={() => void removeCartItem(item.id)}>حذف</button></div></article>; })}</section><aside className="summary-card"><h2>ملخص الطلب</h2><div className="summary-line"><span>المجموع</span><b>{money(cart.subtotal_cents)}</b></div><div className="summary-line"><span>الخصم</span><b>− {money(cart.discount_cents)}</b></div><div className="summary-line"><span>الضريبة</span><b>{money(cart.tax_cents)}</b></div><div className="summary-line"><span>الشحن</span><b>{cart.shipping_cents ? money(cart.shipping_cents) : "مجاني"}</b></div><div className="summary-line total"><span>الإجمالي</span><b>{money(cart.total_cents)}</b></div>{cart.coupon_code ? <div className="alert success">الرمز: {cart.coupon_code} <button className="danger-button" onClick={() => void removeCoupon()}>إزالة</button></div> : <form className="coupon-row" onSubmit={coupon}><input name="code" placeholder="WELCOME10" required/><button>تطبيق</button></form>}<Link className="primary-button" href="/checkout">متابعة الدفع</Link></aside></div></main>;
}
