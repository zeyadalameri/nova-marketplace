"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage, formatMoney } from "@/lib/client-api";
import type { Order } from "@/lib/types";

const labels: Record<string,string> = { pending:"بانتظار المراجعة", confirmed:"تم التأكيد", processing:"قيد التجهيز", shipped:"تم الشحن", delivered:"تم التسليم", cancelled:"ملغي", paid:"مدفوع", unpaid:"غير مدفوع", refunded:"مسترجع" };
export default function OrderDetailPage() {
  const { id } = useParams<{id:string}>(); const { user, language } = useStore(); const [order, setOrder] = useState<Order|null>(null); const [message,setMessage]=useState("");
  async function load() { try { setOrder(await apiRequest<Order>(`/orders/${id}/`)); } catch(error){ setMessage(errorMessage(error)); } }
  useEffect(() => { if(user) void load(); }, [user,id]); // eslint-disable-line react-hooks/exhaustive-deps
  async function action(path:string, success:string){ try { await apiRequest(path,{method:"POST",body:JSON.stringify({})}); setMessage(success); await load(); } catch(error){setMessage(errorMessage(error));} }
  async function requestReturn(event:FormEvent<HTMLFormElement>){event.preventDefault();const formElement=event.currentTarget;const reason=String(new FormData(formElement).get("reason"));try{await apiRequest("/returns/",{method:"POST",body:JSON.stringify({order_id:id,reason})});setMessage("تم إرسال طلب الإرجاع.");formElement.reset();}catch(error){setMessage(errorMessage(error));}}
  if(!user)return <main className="page container"><div className="empty-state"><h1>سجّل الدخول</h1><Link className="primary-button" href="/login">دخول</Link></div></main>;
  if(!order)return <main className="page container"><div className="loading">{message||"جارٍ تحميل الطلب…"}</div></main>;
  const money=(value:number)=>formatMoney(value,order.currency,language==="ar"?"ar-SA":"en-US");
  return <main className="page container"><div className="page-heading"><p className="eyebrow">تفاصيل الطلب</p><h1>{order.invoice_number}</h1><p>{new Date(order.created_at).toLocaleString("ar-SA")}</p></div>{message&&<div className={message.includes("تم")?"alert success":"alert error"}>{message}</div>}<div className="checkout-grid"><section className="panel"><div className="order-head"><h2>الحالة</h2><span className="status">{labels[order.status]??order.status}</span></div><p>الدفع: <b>{labels[order.payment_status]??order.payment_status}</b></p>{order.items.map((item)=><div className="order-item-line" key={item.id}><span>{item.product_name} {item.variant_name&&`(${item.variant_name})`} × {item.quantity}</span><b>{money(item.line_total_cents)}</b></div>)}<h3>عنوان الشحن</h3><p>{order.full_name} · {order.phone}<br/>{order.city}، {order.address}</p>{order.shipment&&<div className="alert success"><b>رقم التتبع: {order.shipment.tracking_number}</b><br/>الحالة: {labels[order.shipment.status]??order.shipment.status}</div>}<div className="stack-actions">{["pending","confirmed"].includes(order.status)&&<button className="danger-button action-button" onClick={()=>void action(`/orders/${id}/cancel/`,"تم إلغاء الطلب.")}>إلغاء الطلب</button>}{order.latest_payment?.status==="pending"&&<button className="primary-button" onClick={()=>void action(`/payments/${order.latest_payment!.public_id}/sandbox_confirm/`,"تم تأكيد الدفع.")}>إكمال الدفع التجريبي</button>}</div>{["shipped","delivered"].includes(order.status)&&<form className="form-card" onSubmit={requestReturn}><h3>طلب إرجاع</h3><textarea name="reason" required placeholder="سبب الإرجاع"/><button>إرسال الطلب</button></form>}</section><aside className="summary-card"><h2>الفاتورة</h2><div className="summary-line"><span>المنتجات</span><b>{money(order.subtotal_cents)}</b></div><div className="summary-line"><span>الخصم</span><b>− {money(order.discount_cents)}</b></div><div className="summary-line"><span>الضريبة</span><b>{money(order.tax_cents)}</b></div><div className="summary-line"><span>الشحن</span><b>{money(order.shipping_cents)}</b></div><div className="summary-line total"><span>الإجمالي</span><b>{money(order.total_cents)}</b></div></aside></div></main>;
}
