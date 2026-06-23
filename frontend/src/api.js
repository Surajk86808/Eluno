const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

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
  inventoryForecast: () => request("/inventory/forecast"),
  analytics: () => request("/analytics/operations"),
  alerts: () => request("/alerts"),
  referenceData: () => request("/orders/meta/reference-data"),
  updateOrderStatus: (orderId, payload) =>
    request(`/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  delayHistory: (orderId) => request(`/orders/${orderId}/delay-history`),

  // Feature 1: Chat agent
  chat: (message, conversationId) =>
    request("/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),

  // Feature 4: Excel export (returns a blob, not JSON)
  exportInventoryExcel: async () => {
    const response = await fetch(`${API_BASE_URL}/inventory/export-excel`);
    if (!response.ok) throw new Error(`Export failed: ${response.status}`);
    return response.blob();
  },

  // Feature 4: Excel import (multipart form)
  importInventoryExcel: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/inventory/import-excel`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail || `Import failed: ${response.status}`);
    }
    return response.json();
  },
};
