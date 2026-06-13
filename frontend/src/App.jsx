import { Activity, AlertTriangle, Boxes, Clock, Edit3, History, LayoutDashboard, LineChart, PackageCheck, Save, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "inventory", label: "Inventory", icon: Boxes },
  { id: "orders", label: "Orders", icon: PackageCheck },
  { id: "analytics", label: "Analytics", icon: LineChart },
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
              <th className="px-4 py-3">Probability</th>
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
                <td className="px-4 py-3 font-medium text-ink">{order.breach_probability}%</td>
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

function Dashboard({ summary, activeOrders }) {
  return (
    <section className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Total Orders" value={summary?.total_orders ?? 0} icon={PackageCheck} />
        <Stat label="Active Orders" value={summary?.active_orders ?? 0} icon={Activity} tone="signal" />
        <Stat label="Delayed Orders" value={summary?.delayed_orders ?? 0} icon={AlertTriangle} tone="danger" />
        <Stat label="High Risk Orders" value={summary?.high_risk_orders ?? 0} icon={AlertTriangle} tone="danger" />
        <Stat label="Inventory Available" value={summary?.inventory_available ?? 0} icon={Boxes} tone="signal" />
        <Stat label="Inventory Shortages" value={summary?.inventory_shortage_orders ?? 0} icon={Boxes} tone="warning" />
        <Stat label="Low Stock Items" value={summary?.low_stock_items ?? 0} icon={Boxes} tone="warning" />
        <Stat label="Avg SLA Left" value={`${averageRemainingHours(activeOrders)}h`} icon={Clock} />
      </div>
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">Active Order Queue</h2>
          <span className="text-sm text-slate-500">{activeOrders.length} open orders</span>
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

  const lowStock = inventory.filter((item) => item.quantity <= item.reorder_level);

  async function checkAvailability() {
    setAvailability(await api.inventoryCheck(lensType, power));
  }

  return (
    <section className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
        <div className="rounded-lg border border-line bg-white p-4">
          <h2 className="text-lg font-semibold text-ink">Inventory Availability</h2>
          <div className="mt-4 space-y-3">
            <select className="field" value={lensType} onChange={(event) => setLensType(event.target.value)}>
              {refs.lens_types.map((type) => <option key={type}>{type}</option>)}
            </select>
            <input className="field" type="number" step="0.5" value={power} onChange={(event) => setPower(event.target.value)} />
            <button className="btn-primary" onClick={checkAvailability}>
              <Search className="h-4 w-4" /> Check
            </button>
          </div>
          {availability && (
            <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm">
              {availability.exists ? `${availability.available_quantity} units available` : "Power not found in inventory"}
            </div>
          )}
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

function Orders({ orders, refs, filters, setFilters, onUpdateStatus, onViewDelayHistory }) {
  return (
    <section className="space-y-4">
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
  const [refs, setRefs] = useState({ lens_types: [], order_statuses: [], store_locations: [] });
  const [filters, setFilters] = useState({ status: "", lens_type: "", store_location: "" });
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [delayHistoryState, setDelayHistoryState] = useState(null);
  const [error, setError] = useState("");

  async function refreshData(currentFilters = filters) {
    const [summaryData, activeOrderData, orderData, inventoryData, analyticsData, referenceData] = await Promise.all([
      api.summary(),
      api.activeOrders(),
      api.orders(currentFilters),
      api.inventory(),
      api.analytics(),
      api.referenceData(),
    ]);
    setSummary(summaryData);
    setActiveOrders(activeOrderData);
    setOrders(orderData);
    setInventory(inventoryData);
    setAnalytics(analyticsData);
    setRefs(referenceData);
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
        />
      );
    }
    if (activeTab === "analytics") return <Analytics analytics={analytics} />;
    return <Dashboard summary={summary} activeOrders={activeOrders} />;
  }, [activeTab, activeOrders, analytics, filters, inventory, orders, refs, summary]);

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
                <Icon className="h-4 w-4" /> {label}
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
    </div>
  );
}
