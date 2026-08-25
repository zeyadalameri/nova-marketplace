"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { useStore } from "@/components/StoreProvider";
import { apiRequest, errorMessage, formatMoney } from "@/lib/client-api";
import type { InventoryDashboard, InventoryInsight } from "@/lib/types";

const kindLabels: Record<string, string> = {
  opening: "رصيد افتتاحي", sale: "بيع", cancellation: "إلغاء", restock: "توريد",
  adjustment: "تسوية", return: "مرتجع", expired: "إتلاف",
};

export default function AIInventoryDashboardPage() {
  const { user, sessionLoading } = useStore();
  const [dashboard, setDashboard] = useState<InventoryDashboard | null>(null);
  const [insight, setInsight] = useState<InventoryInsight | null>(null);
  const [days, setDays] = useState(30);
  const [focus, setFocus] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load(period = days) {
    try { setDashboard(await apiRequest<InventoryDashboard>(`/admin/inventory/dashboard/?days=${period}`)); }
    catch (error) { setMessage(errorMessage(error)); }
  }

  useEffect(() => { if (user?.is_staff) void load(days); }, [user, days]); // eslint-disable-line react-hooks/exhaustive-deps

  async function analyze() {
    setBusy(true); setMessage("");
    try { setInsight(await apiRequest<InventoryInsight>("/admin/inventory/analyze/", { method: "POST", body: JSON.stringify({ days, focus }) })); }
    catch (error) { setMessage(errorMessage(error)); }
    finally { setBusy(false); }
  }

  async function scan() {
    setBusy(true); setMessage("");
    try {
      setDashboard(await apiRequest<InventoryDashboard>("/admin/inventory/scan/", { method: "POST", body: JSON.stringify({}) }));
      setMessage("تم فحص المخزون وإرسال التنبيهات الجديدة.");
    } catch (error) { setMessage(errorMessage(error)); }
    finally { setBusy(false); }
  }

  async function acknowledge(id: number) {
    try { await apiRequest(`/admin/inventory/alerts/${id}/acknowledge/`, { method: "POST", body: JSON.stringify({}) }); await load(); }
    catch (error) { setMessage(errorMessage(error)); }
  }

  async function adjust(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const [product, variant] = String(form.get("target")).split(":");
    const payload = {
      product: Number(product), variant: variant ? Number(variant) : null,
      quantity_delta: Number(form.get("quantity_delta")), kind: String(form.get("kind")),
      reason: String(form.get("reason")), lot_number: String(form.get("lot_number")),
      expires_at: String(form.get("expires_at")) || null,
      unit_cost_cents: Math.round(Number(form.get("unit_cost")) * 100),
    };
    setBusy(true); setMessage("");
    try {
      await apiRequest("/admin/inventory/adjust/", { method: "POST", body: JSON.stringify(payload) });
      setMessage("تم تسجيل الحركة وتحديث المخزون."); formElement.reset(); await load();
    } catch (error) { setMessage(errorMessage(error)); }
    finally { setBusy(false); }
  }

  const maxMovement = useMemo(() => Math.max(1, ...(dashboard?.movements_by_day.map((row) => Math.max(row.sales, row.incoming)) ?? [1])), [dashboard]);

  if (sessionLoading) return <main className="page container"><div className="loading">جارٍ التحقق من الصلاحيات…</div></main>;
  if (!user?.is_staff) return <main className="page container"><div className="empty-state"><h1>هذه اللوحة للموظفين فقط</h1><p>ادخل بحساب مدير أو موظف لديه صلاحية.</p></div></main>;
  if (!dashboard) return <main className="page container"><div className="loading">جارٍ تحليل بيانات المخزون…</div></main>;

  const money = (value: number) => formatMoney(value, "SAR", "ar-SA");
  return <main className="page container ai-admin-page">
    <div className="admin-hero"><div><p className="eyebrow">NOVA AI OPERATIONS</p><h1>مركز قيادة المخزون الذكي</h1><p>مبيعات، مخزون، صلاحية، حركة أصناف وتوصيات عملية من مكان واحد.</p></div><div className="stack-actions"><select aria-label="فترة التحليل" value={days} onChange={(event) => setDays(Number(event.target.value))}><option value={7}>7 أيام</option><option value={30}>30 يومًا</option><option value={90}>90 يومًا</option></select><button className="secondary-button action-button" onClick={() => void scan()} disabled={busy}>فحص وإشعار الآن</button></div></div>
    {message && <div className={message.includes("تم") ? "alert success" : "alert error"}>{message}</div>}

    <section className="metric-grid"><article><span>وحدات المخزون</span><strong>{dashboard.overview.total_stock}</strong><small>{dashboard.overview.products} صنف/متغير</small></article><article><span>قيمة المخزون</span><strong>{money(dashboard.overview.inventory_value_cents)}</strong><small>بسعر البيع الحالي</small></article><article><span>المباع خلال الفترة</span><strong>{dashboard.overview.sold_units}</strong><small>{money(dashboard.overview.revenue_cents)}</small></article><article className={dashboard.overview.active_alerts ? "critical" : ""}><span>تنبيهات نشطة</span><strong>{dashboard.overview.active_alerts}</strong><small>{dashboard.overview.low_stock_items} منخفض/نافد</small></article></section>

    <section className="ai-command-grid"><div className="panel ai-insight-panel"><div className="section-title"><div><p className="eyebrow">المحلل الذكي</p><h2>قرار اليوم</h2></div>{insight && <span>{insight.source === "openai" ? "OpenAI" : "تحليل محلي"}</span>}</div><textarea aria-label="تركيز التحليل" value={focus} onChange={(event) => setFocus(event.target.value)} placeholder="مثال: ركز على المنتجات التي ستنفد خلال أسبوعين" rows={2}/><button className="primary-button" onClick={() => void analyze()} disabled={busy}>{busy ? "جارٍ التحليل…" : "حلّل المخزون بالذكاء الاصطناعي"}</button>{insight ? <div className="insight-result"><p>{insight.summary}</p>{insight.priorities.map((item, index) => <article key={`${item.title}-${index}`}><b>{item.title}</b><span className={`urgency ${item.urgency}`}>{item.urgency}</span><p>{item.reason}</p><strong>{item.action}</strong></article>)}{insight.opportunities.length > 0 && <><h3>فرص</h3><ul>{insight.opportunities.map((item) => <li key={item}>{item}</li>)}</ul></>}{insight.risks.length > 0 && <><h3>مخاطر</h3><ul>{insight.risks.map((item) => <li key={item}>{item}</li>)}</ul></>}</div> : <p className="muted-copy">تعمل التوصيات المحلية دون مفتاح. عند إضافة OPENAI_API_KEY تحصل على تفسير أعمق ومنظم للبيانات.</p>}</div><div className="panel"><div className="section-title"><h2>التنبيهات</h2><span>{dashboard.alerts.length}</span></div><div className="alert-feed">{dashboard.alerts.map((alert) => <article className={`inventory-alert ${alert.severity}`} key={alert.id}><div><b>{alert.severity === "critical" ? "حرج" : alert.severity === "warning" ? "تحذير" : "معلومة"}</b><p>{alert.message}</p></div>{!alert.acknowledged && <button onClick={() => void acknowledge(alert.id)}>تمت المراجعة</button>}</article>)}{!dashboard.alerts.length && <div className="empty-mini">لا توجد تنبيهات نشطة.</div>}</div></div></section>

    <section className="panel movement-panel"><div className="section-title"><h2>حركة الكميات</h2><span>{days} يومًا</span></div><div className="movement-chart">{dashboard.movements_by_day.map((row) => <div className="movement-day" key={row.day}><small>{new Date(row.day).toLocaleDateString("ar-SA", { month: "short", day: "numeric" })}</small><div className="bars"><i className="sales" style={{ height: `${Math.max(4, row.sales / maxMovement * 100)}%` }} title={`مبيعات ${row.sales}`}/><i className="incoming" style={{ height: `${Math.max(4, row.incoming / maxMovement * 100)}%` }} title={`وارد ${row.incoming}`}/></div><b>{row.sales}</b></div>)}{!dashboard.movements_by_day.length && <div className="empty-mini">ستظهر الحركة هنا بعد أول بيع أو توريد.</div>}</div><div className="chart-legend"><span><i className="sales"/> مبيعات</span><span><i className="incoming"/> وارد</span></div></section>

    <section className="admin-table-section panel"><div className="section-title"><h2>الأصناف والتنبؤ بالنفاد</h2><span>{dashboard.stock.length}</span></div><div className="table-scroll"><table><thead><tr><th>الصنف</th><th>SKU</th><th>المخزون</th><th>المباع</th><th>أيام حتى النفاد</th><th>الحالة</th><th>اقتراح التوريد</th></tr></thead><tbody>{dashboard.stock.map((row) => <tr key={`${row.product_id}-${row.variant_id ?? 0}`}><td><b>{row.name}</b>{row.variant_name && <small>{row.variant_name}</small>}</td><td dir="ltr">{row.sku}</td><td>{row.stock}</td><td>{row.sold_units}</td><td>{row.days_to_stockout ?? "—"}</td><td><span className={`stock-state ${row.status}`}>{row.status === "healthy" ? "جيد" : row.status === "low" ? "منخفض" : "نافد"}</span></td><td>{row.reorder_quantity}</td></tr>)}</tbody></table></div></section>

    <section className="ai-command-grid"><form className="panel inventory-adjust-form" onSubmit={adjust}><h2>تسجيل توريد أو تسوية</h2><label>الصنف<select name="target" required>{dashboard.stock.map((row) => <option key={`${row.product_id}:${row.variant_id ?? ""}`} value={`${row.product_id}:${row.variant_id ?? ""}`}>{row.sku} — {row.name} {row.variant_name}</option>)}</select></label><div className="form-grid"><label>تغير الكمية<input name="quantity_delta" type="number" required placeholder="مثال: 20 أو -2"/></label><label>نوع الحركة<select name="kind"><option value="restock">توريد</option><option value="adjustment">تسوية</option><option value="return">مرتجع</option><option value="expired">إتلاف منتهي</option></select></label><label>رقم الدفعة<input name="lot_number" placeholder="اختياري"/></label><label>تاريخ الصلاحية<input name="expires_at" type="date"/></label><label>تكلفة الوحدة (ر.س)<input name="unit_cost" type="number" min="0" step="0.01" defaultValue="0"/></label><label>السبب<input name="reason" placeholder="فاتورة المورد أو سبب التسوية"/></label></div><button className="primary-button" disabled={busy}>حفظ الحركة</button></form><div className="panel"><div className="section-title"><h2>الصلاحية</h2><span>{dashboard.expiring_batches.length}</span></div>{dashboard.expiring_batches.map((batch) => <article className={`expiry-row ${batch.days_left < 0 ? "expired" : ""}`} key={batch.id}><div><b>{batch.product} {batch.variant}</b><small>الدفعة {batch.lot_number}</small></div><strong>{batch.quantity} وحدة</strong><span>{batch.days_left < 0 ? `منتهية منذ ${Math.abs(batch.days_left)} يوم` : `متبقي ${batch.days_left} يوم`}</span></article>)}{!dashboard.expiring_batches.length && <div className="empty-mini">لا توجد دفعات قريبة الانتهاء.</div>}</div></section>

    <section className="panel admin-table-section"><div className="section-title"><h2>آخر حركات المخزون</h2><span>{dashboard.recent_movements.length}</span></div><div className="table-scroll"><table><thead><tr><th>الوقت</th><th>الصنف</th><th>النوع</th><th>التغير</th><th>الرصيد</th><th>السبب</th></tr></thead><tbody>{dashboard.recent_movements.map((movement) => <tr key={movement.id}><td>{new Date(movement.created_at).toLocaleString("ar-SA")}</td><td>{movement.sku} — {movement.product}</td><td>{kindLabels[movement.kind] ?? movement.kind}</td><td className={movement.quantity_delta > 0 ? "positive-number" : "negative-number"}>{movement.quantity_delta > 0 ? "+" : ""}{movement.quantity_delta}</td><td>{movement.stock_after}</td><td>{movement.reason}</td></tr>)}</tbody></table></div></section>
  </main>;
}
