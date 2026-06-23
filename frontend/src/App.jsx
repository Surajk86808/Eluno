import { Activity, AlertTriangle, Boxes, Clock, Edit3, History, LayoutDashboard, LineChart, MessageSquare, PackageCheck, Save, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import PrescriptionUpload from "./components/PrescriptionUpload";
import Alerts from "./pages/Alerts";
import Chat from "./pages/Chat";
import InvoiceUpload from "./pages/InvoiceUpload";

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "inventory", label: "Inventory", icon: Boxes },
  { id: "orders", label: "Orders", icon: PackageCheck },
  { id: "analytics", label: "Analytics", icon: LineChart },
  { id: "alerts", label: "Alerts" },
  { id: "chat", label: "Copilot", icon: MessageSquare },
  { id: "invoice", label: "Invoice Parser" },
];

function Stat({ label, value, icon: Icon, tone = "default" }) {
  const tones = {
    default: "border-line bg-white text-ink",
    signal: "border-teal-200 bg-teal-50 text-signal",
    warning: "border-amber-200 bg-amber-50 text-warning",
    danger: "border-red-200 bg-red-50 text-danger",
  };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-600">{label}</p>
        <Icon className="h-5 w-5" />
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-normal">{value}</p>
    </div>
  );
}

function RiskPill({ risk }) {
  const styles = {
    High: "bg-red-100 text-red-800",
    Medium: "bg-amber-100 text-amber-800",
    Low: "bg-teal-100 text-teal-800",
  };
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[risk] || styles.Low}`}>{risk}</span>;
}

function averageRemainingHours(orders) {
  if (!orders.length) return 0;
  const total = orders.reduce((sum, order) => sum + Number(order.remaining_sla_hours || 0), 0);
  return Math.round((total / orders.length) * 10) / 10;
}

function OrderTable({ orders, onUpdateStatus, onViewDelayHistory }) {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Lens</th>
              <th className="px-4 py-3">Frame</th>
              <th className="px-4 py-3">Store</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">SLA Left</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Breach %</th>
              <th className="px-4 py-3">Delay Reason</th>
              {(onUpdateStatus || onViewDelayHistory) && <th className="px-4 py-3">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-ink">{order.customer_name}</td>
                <td className="px-4 py-3">{order.lens_type} ({order.power})</td>
                <td className="px-4 py-3">{order.frame_name}</td>
                <td className="px-4 py-3">{order.store_location}</td>
                <td className="px-4 py-3">{order.status}</td>
                <td className="px-4 py-3">{order.remaining_sla_hours}h</td>
                <td className="px-4 py-3"><RiskPill risk={order.risk_level} /></td>
                <td className="px-4 py-3 font-medium text-ink">{order.breach_percentage}%</td>
                <td className="px-4 py-3">{order.latest_delay_reason}</td>
                {(onUpdateStatus || onViewDelayHistory) && (
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {onUpdateStatus && (
                        <button className="icon-button" onClick={() => onUpdateStatus(order)} title="Update status">
                          <Edit3 className="h-4 w-4" />
                        </button>
                      )}
                      {onViewDelayHistory && (
                        <button className="btn-secondary whitespace-nowrap" onClick={() => onViewDelayHistory(order)}>
                          <History className="h-4 w-4" /> View Delay History
                        </button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Dashboard({ summary, activeOrders, onNewOrderViaPrescription }) {
  const allActiveAreDelayed =
    summary &&
    summary.active_orders > 0 &&
    summary.delayed_orders >= summary.active_orders;

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-6 rounded-xl border border-line shadow-sm">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-ink">Operational Overview</h2>
          <p className="text-sm text-slate-500">Monitor order health and lens inventory in real-time</p>
        </div>
        <button 
          className="btn-primary py-3 px-6 text-base font-semibold shadow-md hover:shadow-lg transition-all" 
          type="button" 
          onClick={onNewOrderViaPrescription}
        >
          <PackageCheck className="h-5 w-5" /> New Order via Prescription
        </button>
      </div>

      {/* Historical data notice */}
      {allActiveAreDelayed && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <div>
            <span className="font-semibold">Historical dataset:</span> SLA timers run from each order's original creation date.
            Orders older than their SLA window (48h / 72h / 96h) are counted as breached.
            This is expected for imported or demo data — new orders you create today will show accurate SLA countdowns.
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Total Orders" value={summary?.total_orders ?? 0} icon={PackageCheck} />
        <Stat label="Active Orders" value={summary?.active_orders ?? 0} icon={Activity} tone="signal" />
        <Stat label="SLA Breached" value={summary?.delayed_orders ?? 0} icon={AlertTriangle} tone="danger" />
        <Stat label="High Risk Orders" value={summary?.high_risk_orders ?? 0} icon={AlertTriangle} tone="danger" />
        <Stat label="Inventory Available" value={summary?.inventory_available ?? 0} icon={Boxes} tone="signal" />
        <Stat label="Inventory Shortages" value={summary?.inventory_shortage_orders ?? 0} icon={Boxes} tone="warning" />
        <Stat label="Low Stock Items" value={summary?.low_stock_items ?? 0} icon={Boxes} tone="warning" />
        <Stat label="Avg SLA Left" value={`${averageRemainingHours(activeOrders)}h`} icon={Clock} />
      </div>

      <div className="pt-2">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">Active Order Queue</h2>
          <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {activeOrders.length} open orders
          </span>
        </div>
        <OrderTable orders={activeOrders.slice(0, 12)} />
      </div>
    </section>
  );
}

function Inventory({ inventory, refs }) {
  const [lensType, setLensType] = useState("Single Vision");
  const [power, setPower] = useState("-2.0");
  const [availability, setAvailability] = useState(null);
  const [inventoryTab, setInventoryTab] = useState("stock"); // "stock" | "forecast"
  const [forecasts, setForecasts] = useState([]);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importError, setImportError] = useState("");
  const [exportLoading, setExportLoading] = useState(false);

  const lowStock = inventory.filter((item) => item.quantity <= item.reorder_level);

  function handleLensTypeChange(event) {
    setLensType(event.target.value);
    setAvailability(null);
  }

  function handlePowerChange(event) {
    setPower(event.target.value);
    setAvailability(null);
  }

  async function checkAvailability() {
    setAvailability(await api.inventoryCheck(lensType, power));
  }

  async function loadForecast() {
    if (forecasts.length > 0) return; // cached
    setForecastLoading(true);
    try {
      const data = await api.inventoryForecast();
      setForecasts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setForecastLoading(false);
    }
  }

  function handleTabChange(tab) {
    setInventoryTab(tab);
    if (tab === "forecast") loadForecast();
  }

  async function handleExport() {
    setExportLoading(true);
    try {
      const blob = await api.exportInventoryExcel();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "inventory.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    } finally {
      setExportLoading(false);
    }
  }

  async function handleImport(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImportResult(null);
    setImportError("");
    try {
      const result = await api.importInventoryExcel(file);
      setImportResult(result);
    } catch (err) {
      setImportError(err.message);
    }
    // Reset file input
    event.target.value = "";
  }

  // Recharts bar chart for forecast
  function ForecastChart({ data }) {
    // Only show items with days_remaining (exclude null)
    const chartData = data
      .filter((d) => d.days_remaining !== null)
      .slice(0, 15)
      .map((d) => ({
        name: `${d.lens_type} (${d.power})`,
        days: d.days_remaining,
        fill: d.days_remaining <= 7 ? "#b91c1c" : d.days_remaining <= 30 ? "#b45309" : "#0f766e",
      }));

    if (chartData.length === 0) return <p className="text-sm text-slate-500">No consumption data available yet.</p>;

    const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } = window.Recharts || {};

    // If recharts not available via window, use a simple visual bar
    return (
      <div className="space-y-2">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-3 text-sm">
            <span className="w-48 shrink-0 truncate text-slate-600" title={item.name}>{item.name}</span>
            <div className="flex-1 rounded-full bg-slate-100 h-4 overflow-hidden">
              <div
                className="h-4 rounded-full transition-all"
                style={{
                  width: `${Math.min((item.days / 90) * 100, 100)}%`,
                  backgroundColor: item.fill,
                }}
              />
            </div>
            <span className="w-20 text-right font-semibold" style={{ color: item.fill }}>
              {item.days}d
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="space-y-5">
      {/* Toolbar: Import / Export */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2 border border-line rounded-lg overflow-hidden bg-white">
          {["stock", "forecast"].map((tab) => (
            <button
              key={tab}
              className={`px-4 py-2 text-sm font-medium transition ${
                inventoryTab === tab ? "bg-signal text-white" : "text-slate-600 hover:bg-slate-50"
              }`}
              onClick={() => handleTabChange(tab)}
            >
              {tab === "stock" ? "Stock" : "Forecast"}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <label className="btn-secondary cursor-pointer">
            <span>Import Excel</span>
            <input type="file" accept=".xlsx" onChange={handleImport} className="hidden" />
          </label>
          <button className="btn-secondary" onClick={handleExport} disabled={exportLoading}>
            {exportLoading ? "Exporting…" : "Export Excel"}
          </button>
        </div>
      </div>

      {importResult && (
        <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Imported {importResult.imported} rows of {importResult.total_rows} total.
          {importResult.errors.length > 0 && (
            <ul className="mt-1 list-disc list-inside text-red-700">
              {importResult.errors.map((e, i) => <li key={i}>Row {e.row}: {e.error}</li>)}
            </ul>
          )}
        </div>
      )}
      {importError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{importError}</div>
      )}

      {/* Stock tab */}
      {inventoryTab === "stock" && (
        <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
          <div className="rounded-lg border border-line bg-white p-4">
            <h2 className="text-lg font-semibold text-ink">Inventory Availability</h2>
            <div className="mt-4 space-y-3">
              <select className="field" value={lensType} onChange={handleLensTypeChange}>
                {refs.lens_types.map((type) => <option key={type}>{type}</option>)}
              </select>
              <input className="field" type="number" step="0.5" value={power} onChange={handlePowerChange} />
              <button className="btn-primary" onClick={checkAvailability}>
                Check
              </button>
              {availability && (
                <div
                  className={`border-l-4 px-3 py-2 text-sm font-medium ${
                    availability.in_stock ? "border-green-600 bg-green-50 text-green-800" : "border-red-600 bg-red-50 text-red-800"
                  }`}
                >
                  {availability.in_stock
                    ? `In Stock — Qty: ${availability.quantity}`
                    : "Out of Stock — will need to order"}
                </div>
              )}
            </div>
          </div>
          <div className="rounded-lg border border-line bg-white p-4">
            <h2 className="text-lg font-semibold text-ink">Low Stock Watchlist</h2>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {lowStock.slice(0, 12).map((item) => (
                <div key={item.id} className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm">
                  <p className="font-semibold text-warning">{item.lens_type}</p>
                  <p>Power {item.power} | Qty {item.quantity}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Forecast tab */}
      {inventoryTab === "forecast" && (
        <div className="rounded-xl border border-line bg-white p-5 space-y-5">
          <div>
            <h2 className="text-lg font-semibold text-ink">Stockout Forecast</h2>
            <p className="text-sm text-slate-500 mt-0.5">Based on 60-day consumption rate · sorted by urgency</p>
          </div>

          {forecastLoading && <p className="text-sm text-slate-500">Computing forecasts…</p>}

          {!forecastLoading && forecasts.length > 0 && (
            <>
              {/* Visual bar chart */}
              <div className="rounded-lg border border-line p-4">
                <h3 className="text-sm font-semibold text-slate-500 uppercase mb-3">Days Until Stockout</h3>
                <ForecastChart data={forecasts} />
              </div>

              {/* Detailed table */}
              <div className="overflow-x-auto rounded-lg border border-line">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 border-b border-line">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Lens Type</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Power</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Stock</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Avg/Day</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Days Left</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Stockout Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {forecasts.map((item) => {
                      const urgent = item.days_remaining !== null && item.days_remaining <= 7;
                      const warning = item.days_remaining !== null && item.days_remaining <= 30 && !urgent;
                      return (
                        <tr key={item.sku_id} className={`hover:bg-slate-50 ${urgent ? "bg-red-50" : warning ? "bg-amber-50" : ""}`}>
                          <td className="px-4 py-2 font-medium text-ink">{item.lens_type}</td>
                          <td className="px-4 py-2">{item.power}</td>
                          <td className="px-4 py-2">{item.current_stock}</td>
                          <td className="px-4 py-2">{item.avg_daily_consumption}</td>
                          <td className={`px-4 py-2 font-semibold ${urgent ? "text-danger" : warning ? "text-warning" : "text-signal"}`}>
                            {item.days_remaining !== null ? `${item.days_remaining}d` : "—"}
                          </td>
                          <td className="px-4 py-2 text-slate-500">{item.predicted_stockout_date || "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

function StatusModal({ order, refs, onClose, onSubmit }) {
  const [status, setStatus] = useState(order.status);
  const [reason, setReason] = useState("");

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/40 px-4">
      <div className="w-full max-w-md rounded-lg border border-line bg-white p-5 shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-ink">Update Order #{order.id}</h2>
            <p className="text-sm text-slate-500">{order.customer_name}</p>
          </div>
          <button className="icon-button" onClick={onClose} title="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-4 space-y-3">
          <select className="field" value={status} onChange={(event) => setStatus(event.target.value)}>
            {refs.order_statuses.map((item) => <option key={item}>{item}</option>)}
          </select>
          <textarea
            className="field min-h-28 resize-y"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Delay reason"
          />
          <button className="btn-primary" onClick={() => onSubmit(order.id, { status, reason: reason.trim() || null })}>
            <Save className="h-4 w-4" /> Save Status
          </button>
        </div>
      </div>
    </div>
  );
}

function DelayHistoryModal({ order, history, onClose }) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/40 px-4">
      <div className="w-full max-w-lg rounded-lg border border-line bg-white p-5 shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-ink">Delay History #{order.id}</h2>
            <p className="text-sm text-slate-500">{order.customer_name}</p>
          </div>
          <button className="icon-button" onClick={onClose} title="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-4 space-y-2">
          {history.length ? (
            history.map((item) => (
              <div key={item.id} className="rounded-md border border-line bg-slate-50 px-3 py-2 text-sm">
                <p className="font-medium text-ink">{item.reason}</p>
                <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
              </div>
            ))
          ) : (
            <div className="rounded-md bg-slate-50 p-3 text-sm text-slate-500">No delay history recorded.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function PrescriptionUploadModal({ onClose, onOrderCreated }) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/50 px-4">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-2xl flex flex-col max-h-[90vh]">
        <div className="p-5 border-b border-line flex items-center justify-between shrink-0">
          <h2 className="text-xl font-bold text-ink">New Order via Prescription</h2>
          <button className="icon-button" onClick={onClose} title="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto">
          <PrescriptionUpload onOrderCreated={onOrderCreated} />
        </div>
      </div>
    </div>
  );
}

function NewOrderModal({ draft, refs, onClose, onSubmit }) {
  const [form, setForm] = useState({
    customer_name: "",
    lens_type: draft.lens_type || "Single Vision",
    power: draft.power || "",
    coating: draft.coating || "",
    frame_name: "",
    store_location: refs.store_locations[0] || "",
  });
  const [isSaving, setIsSaving] = useState(false);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit() {
    setIsSaving(true);
    try {
      await onSubmit({
        customer_name: form.customer_name,
        lens_type: form.lens_type,
        power: Number(form.power),
        frame_name: form.frame_name,
        store_location: form.store_location,
      });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/50 px-4">
      <div className="w-full max-w-xl bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">New Order</h2>
          <button className="icon-button" onClick={onClose} title="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="field"
            value={form.customer_name}
            onChange={(event) => updateField("customer_name", event.target.value)}
            placeholder="Customer name"
          />
          <input
            className="field"
            value={form.frame_name}
            onChange={(event) => updateField("frame_name", event.target.value)}
            placeholder="Frame name"
          />
          <select className="field" value={form.lens_type} onChange={(event) => updateField("lens_type", event.target.value)}>
            {refs.lens_types.map((type) => <option key={type}>{type}</option>)}
          </select>
          <input
            className="field"
            type="number"
            step="0.25"
            value={form.power}
            onChange={(event) => updateField("power", event.target.value)}
            placeholder="Power"
          />
          <input
            className="field"
            value={form.coating}
            onChange={(event) => updateField("coating", event.target.value)}
            placeholder="Coating"
          />
          <select className="field" value={form.store_location} onChange={(event) => updateField("store_location", event.target.value)}>
            {refs.store_locations.map((store) => <option key={store}>{store}</option>)}
          </select>
        </div>
        <button className="btn-primary mt-4" type="button" onClick={handleSubmit} disabled={isSaving}>
          {isSaving ? "Creating..." : "Create Order"}
        </button>
      </div>
    </div>
  );
}

function Orders({ orders, refs, filters, setFilters, onUpdateStatus, onViewDelayHistory, onUploadPrescription }) {
  return (
    <section className="space-y-4">
      <div className="flex justify-end">
        <button className="btn-secondary" type="button" onClick={onUploadPrescription}>
          Upload Prescription
        </button>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <select className="field" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
          <option value="">All statuses</option>
          {refs.order_statuses.map((status) => <option key={status}>{status}</option>)}
        </select>
        <select className="field" value={filters.lens_type} onChange={(event) => setFilters({ ...filters, lens_type: event.target.value })}>
          <option value="">All lens types</option>
          {refs.lens_types.map((type) => <option key={type}>{type}</option>)}
        </select>
        <select className="field" value={filters.store_location} onChange={(event) => setFilters({ ...filters, store_location: event.target.value })}>
          <option value="">All stores</option>
          {refs.store_locations.map((store) => <option key={store}>{store}</option>)}
        </select>
      </div>
      <OrderTable orders={orders} onUpdateStatus={onUpdateStatus} onViewDelayHistory={onViewDelayHistory} />
    </section>
  );
}

function Analytics({ analytics }) {
  const sections = [
    ["By Status", analytics?.by_status],
    ["By Lens Type", analytics?.by_lens_type],
    ["By Store", analytics?.by_store],
    ["Risk Levels", analytics?.risk_levels],
  ];
  return (
    <section className="grid gap-4 lg:grid-cols-2">
      {sections.map(([title, values]) => (
        <div key={title} className="rounded-lg border border-line bg-white p-4">
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          <div className="mt-3 space-y-2">
            {Object.entries(values || {}).map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
                <span>{label}</span>
                <span className="font-semibold text-ink">{value}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [activeOrders, setActiveOrders] = useState([]);
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [refs, setRefs] = useState({ lens_types: [], order_statuses: [], store_locations: [] });
  const [filters, setFilters] = useState({ status: "", lens_type: "", store_location: "" });
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [delayHistoryState, setDelayHistoryState] = useState(null);
  const [showPrescriptionUpload, setShowPrescriptionUpload] = useState(false);
  const [prescriptionUploadSource, setPrescriptionUploadSource] = useState(null);
  const [orderDraft, setOrderDraft] = useState(null);
  const [error, setError] = useState("");

  async function refreshData(currentFilters = filters) {
    const [summaryData, activeOrderData, orderData, inventoryData, analyticsData, alertsData, referenceData] = await Promise.all([
      api.summary(),
      api.activeOrders(),
      api.orders(currentFilters),
      api.inventory(),
      api.analytics(),
      api.alerts(),
      api.referenceData(),
    ]);
    setSummary(summaryData);
    setActiveOrders(activeOrderData);
    setOrders(orderData);
    setInventory(inventoryData);
    setAnalytics(analyticsData);
    setAlerts(alertsData);
    setRefs(referenceData);
  }

  async function fetchStats() {
    const summaryData = await api.summary();
    setSummary(summaryData);
  }

  async function fetchOrders(currentFilters = filters) {
    const [activeOrderData, orderData] = await Promise.all([
      api.activeOrders(),
      api.orders(currentFilters),
    ]);
    setActiveOrders(activeOrderData);
    setOrders(orderData);
  }

  function openPrescriptionUpload(source) {
    setPrescriptionUploadSource(source);
    setShowPrescriptionUpload(true);
  }

  useEffect(() => {
    refreshData()
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    api.orders(filters).then(setOrders).catch((err) => setError(err.message));
  }, [filters]);

  async function handleStatusUpdate(orderId, payload) {
    await api.updateOrderStatus(orderId, payload);
    setSelectedOrder(null);
    await refreshData();
  }

  async function handleViewDelayHistory(order) {
    const history = await api.delayHistory(order.id);
    setDelayHistoryState({ order, history });
  }

  async function handleOrderCreatedFromPrescription() {
    if (prescriptionUploadSource === "dashboard") {
      await fetchStats();
      await fetchOrders();
    } else {
      await fetchOrders();
    }
    setShowPrescriptionUpload(false);
    setPrescriptionUploadSource(null);
  }

  async function handleCreateOrder(payload) {
    await api.createOrder(payload);
    setOrderDraft(null);
    await refreshData();
  }

  const page = useMemo(() => {
    if (activeTab === "inventory") return <Inventory inventory={inventory} refs={refs} />;
    if (activeTab === "orders") {
      return (
        <Orders
          orders={orders}
          refs={refs}
          filters={filters}
          setFilters={setFilters}
          onUpdateStatus={setSelectedOrder}
          onViewDelayHistory={(order) => handleViewDelayHistory(order).catch((err) => setError(err.message))}
          onUploadPrescription={() => openPrescriptionUpload("orders")}
        />
      );
    }
    if (activeTab === "analytics") return <Analytics analytics={analytics} />;
    if (activeTab === "alerts") return <Alerts alerts={alerts} />;
    if (activeTab === "chat") return <Chat />;
    if (activeTab === "invoice") return <InvoiceUpload />;
    return (
      <Dashboard
        summary={summary}
        activeOrders={activeOrders}
        onNewOrderViaPrescription={() => openPrescriptionUpload("dashboard")}
      />
    );
  }, [activeTab, activeOrders, alerts, analytics, filters, inventory, orders, refs, summary]);

  return (
    <div className="min-h-screen bg-surface text-slate-700">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal text-ink">Eyewear Order Management</h1>
            <p className="text-sm text-slate-500">SLA-aware operations for prescription lens fulfillment</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} className={`nav-button ${activeTab === id ? "nav-button-active" : ""}`} onClick={() => setActiveTab(id)}>
                {Icon && <Icon className="h-4 w-4" />} {label}
              </button>
            ))}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        {error && <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
        {page}
      </main>
      {selectedOrder && (
        <StatusModal
          order={selectedOrder}
          refs={refs}
          onClose={() => setSelectedOrder(null)}
          onSubmit={(orderId, payload) => handleStatusUpdate(orderId, payload).catch((err) => setError(err.message))}
        />
      )}
      {delayHistoryState && (
        <DelayHistoryModal
          order={delayHistoryState.order}
          history={delayHistoryState.history}
          onClose={() => setDelayHistoryState(null)}
        />
      )}
      {showPrescriptionUpload && (
        <PrescriptionUploadModal
          onClose={() => {
            setShowPrescriptionUpload(false);
            setPrescriptionUploadSource(null);
          }}
          onOrderCreated={() => handleOrderCreatedFromPrescription().catch((err) => setError(err.message))}
        />
      )}
      {orderDraft && (
        <NewOrderModal
          draft={orderDraft}
          refs={refs}
          onClose={() => setOrderDraft(null)}
          onSubmit={(payload) => handleCreateOrder(payload).catch((err) => setError(err.message))}
        />
      )}
    </div>
  );
}
