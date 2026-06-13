const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  summary: () => request("/dashboard/summary"),
  activeOrders: () => request("/dashboard/active-orders"),
  delayedOrders: () => request("/dashboard/delayed-orders"),
  orders: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
    return request(`/orders${query.toString() ? `?${query}` : ""}`);
  },
  createOrder: (payload) =>
    request("/orders", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  inventory: () => request("/inventory"),
  inventoryCheck: (lensType, power) =>
    request(`/inventory/check?lens_type=${encodeURIComponent(lensType)}&power=${encodeURIComponent(power)}`),
  analytics: () => request("/analytics/operations"),
  alerts: () => request("/alerts"),
  referenceData: () => request("/orders/meta/reference-data"),
  updateOrderStatus: (orderId, payload) =>
    request(`/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  delayHistory: (orderId) => request(`/orders/${orderId}/delay-history`),
};
