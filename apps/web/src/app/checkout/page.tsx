"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage, formatMoney } from "@/lib/client-api";
import type { Address, Order, Payment } from "@/lib/types";

export default function CheckoutPage() {
  const { user, cart, currency, refreshCart, language } = useStore(); const router = useRouter();
  const [addresses, setAddresses] = useState<Address[]>([]); const [addressId, setAddressId] = useState<number | null>(null);
  const [paymentMethod, setPaymentMethod] = useState("card"); const [payment, setPayment] = useState<Payment | null>(null); const [order, setOrder] = useState<Order | null>(null);
  const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  const checkoutKey = useRef("");
  useEffect(() => { if (user) void apiRequest<Address[] | { results: Address[] }>("/auth/addresses/").then((payload) => { const list = Array.isArray(payload) ? payload : payload.results; setAddresses(list); setAddressId(list.find((item) => item.is_default)?.id ?? list[0]?.id ?? null); }); }, [user]);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!addressId) return; setBusy(true); setMessage("");
    try {
      if (!checkoutKey.current) checkoutKey.current = crypto.randomUUID();
      const created = await apiRequest<Order>("/orders/", { method: "POST", headers: { "Idempotency-Key": checkoutKey.current }, body: JSON.stringify({ payment_method: paymentMethod, address_id: addressId, currency }) });
      setOrder(created); await refreshCart();
      if (paymentMethod === "card") {
        const initiated = await apiRequest<Payment>(`/orders/${created.public_id}/initiate_payment/`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({}) });
        setPayment(initiated); setMessage("تم إنشاء عملية الدفع. في البيئة المحلية استخدم زر التأكيد التجريبي.");
      } else router.push(`/orders/${created.public_id}`);
    } catch (error) { setMessage(errorMessage(error)); } finally { setBusy(false); }
  }
  async function confirmPayment() {
    if (!payment || !order) return; setBusy(true);
    try { await apiRequest(`/payments/${payment.public_id}/sandbox_confirm/`, { method: "POST", body: JSON.stringify({}) }); router.push(`/orders/${order.public_id}`); }
    catch (error) { setMessage(errorMessage(error)); } finally { setBusy(false); }
  }
  if (!user) return <main className="page container"><div className="empty-state"><h1>سجّل الدخول لإتمام الطلب</h1><Link className="primary-button" href="/login">تسجيل الدخول</Link></div></main>;
  if (!cart?.items.length && !order) return <main className="page container"><div className="empty-state"><h1>السلة فارغة</h1><Link className="primary-button" href="/">العودة للمتجر</Link></div></main>;
  const money = (value: number) => formatMoney(value, cart?.currency ?? currency, language === "ar" ? "ar-SA" : "en-US");
  return <main className="page container"><div className="page-heading"><p className="eyebrow">خطوة أخيرة</p><h1>العنوان والدفع</h1></div>{message && <div className={message.includes("تم") ? "alert success" : "alert error"}>{message}</div>}{payment && order ? <section className="form-card"><h2>الدفع التجريبي</h2><p>الطلب {order.invoice_number}</p><strong className="price-large">{money(payment.amount_cents)}</strong><button onClick={() => void confirmPayment()} disabled={busy}>تأكيد الدفع بنجاح</button><p className="auth-switch">هذا الزر يحاكي Webhook مزود الدفع محليًا فقط.</p></section> : <form className="checkout-grid" onSubmit={submit}><section className="panel"><h2>عنوان الشحن</h2>{addresses.length ? addresses.map((address) => <label className="address-option" key={address.id}><input type="radio" name="address" checked={addressId === address.id} onChange={() => setAddressId(address.id)}/><b>{address.label} — {address.full_name}</b><br/><span>{address.city}، {address.line1} · {address.phone}</span></label>) : <div className="alert error">لا يوجد عنوان محفوظ. <Link href="/account">أضف عنوانًا من حسابك</Link></div>}<h2>طريقة الدفع</h2><label className="address-option"><input type="radio" name="payment" checked={paymentMethod === "card"} onChange={() => setPaymentMethod("card")}/> بطاقة أو محفظة رقمية</label><label className="address-option"><input type="radio" name="payment" checked={paymentMethod === "cod"} onChange={() => setPaymentMethod("cod")}/> الدفع عند الاستلام</label></section><aside className="summary-card"><h2>الإجمالي</h2><div className="summary-line"><span>المنتجات</span><b>{money(cart?.subtotal_cents ?? 0)}</b></div><div className="summary-line"><span>الخصم</span><b>− {money(cart?.discount_cents ?? 0)}</b></div><div className="summary-line"><span>الضريبة</span><b>{money(cart?.tax_cents ?? 0)}</b></div><div className="summary-line"><span>الشحن</span><b>{money(cart?.shipping_cents ?? 0)}</b></div><div className="summary-line total"><span>الإجمالي</span><b>{money(cart?.total_cents ?? 0)}</b></div><button className="primary-button" disabled={!addressId || busy}>{busy ? "جارٍ إنشاء الطلب…" : "تأكيد الطلب"}</button></aside></form>}</main>;
}
