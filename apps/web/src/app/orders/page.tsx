"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, formatMoney } from "@/lib/client-api";
import type { Order, Paginated } from "@/lib/types";

const statusLabels: Record<string,string> = { pending:"بانتظار المراجعة", confirmed:"مؤكد", processing:"قيد التجهيز", shipped:"تم الشحن", delivered:"تم التسليم", cancelled:"ملغي" };
export default function OrdersPage() {
  const { user, language } = useStore(); const [orders, setOrders] = useState<Order[]>([]);
  useEffect(() => { if (user) void apiRequest<Paginated<Order>>("/orders/").then((payload) => setOrders(payload.results)); }, [user]);
  if (!user) return <main className="page container"><div className="empty-state"><h1>سجّل الدخول لمراجعة طلباتك</h1><Link className="primary-button" href="/login">تسجيل الدخول</Link></div></main>;
  return <main className="page container"><div className="page-heading"><p className="eyebrow">سجل مشترياتك</p><h1>طلباتي</h1></div><div className="order-list">{orders.map((order) => <Link href={`/orders/${order.public_id}`} className="order-card" key={order.public_id}><div className="order-head"><div><h3>{order.invoice_number}</h3><small>{new Date(order.created_at).toLocaleDateString("ar-SA")}</small></div><span className="status">{statusLabels[order.status] ?? order.status}</span></div><div className="summary-line"><span>{order.items.length} عناصر</span><b>{formatMoney(order.total_cents, order.currency, language === "ar" ? "ar-SA" : "en-US")}</b></div></Link>)}</div>{!orders.length && <div className="empty-state"><h2>لا توجد طلبات بعد</h2><Link className="primary-button" href="/">ابدأ التسوق</Link></div>}</main>;
}
