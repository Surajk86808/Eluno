type Alert = {
  id: number;
  order_id: number;
  customer_name: string;
  breach_percentage: number;
  alert_type: "Breached" | "High Risk" | string;
  created_at: string;
};

type AlertsProps = {
  alerts: Alert[];
};

function AlertPill({ type }: { type: Alert["alert_type"] }) {
  const className =
    type === "Breached"
      ? "bg-red-100 text-red-800"
      : "bg-orange-100 text-orange-800";

  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}>{type}</span>;
}

export default function Alerts({ alerts }: AlertsProps) {
  if (!alerts.length) {
    return <p className="text-sm text-slate-500">No alerts fired yet.</p>;
  }

  return (
    <section className="overflow-x-auto">
      <table className="min-w-full border-y border-line bg-white text-sm">
        <thead className="border-b border-line bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Order ID</th>
            <th className="px-4 py-3">Customer Name</th>
            <th className="px-4 py-3">Breach %</th>
            <th className="px-4 py-3">Timestamp</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {alerts.map((alert) => (
            <tr key={alert.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 font-medium text-ink">#{alert.order_id}</td>
              <td className="px-4 py-3">{alert.customer_name}</td>
              <td className="px-4 py-3 font-medium text-ink">{alert.breach_percentage}%</td>
              <td className="px-4 py-3">{new Date(alert.created_at).toLocaleString()}</td>
              <td className="px-4 py-3">
                <AlertPill type={alert.alert_type} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
