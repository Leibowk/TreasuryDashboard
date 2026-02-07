const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Order {
  id: number;
  date: string;
  term: string;
  amount: number;
  yield_pct: number;
  status: string;
  created_at: string;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
}

export async function fetchOrders(
  offset: number = 0,
  limit: number = 10
): Promise<OrderListResponse> {
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });
  const res = await fetch(`${API_BASE}/api/orders?${params}`);
  if (!res.ok) {
    throw new Error(`Failed to load orders: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function createOrder(term: string, amount: number): Promise<Order> {
  const res = await fetch(`${API_BASE}/api/order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ term, amount }),
  });
  if (!res.ok) {
    const text = await res.text();
    let message = `Failed to create order: ${res.status} ${res.statusText}`;
    try {
      const j = JSON.parse(text);
      if (j.detail) message = j.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  return res.json();
}

export async function updateOrderStatus(
  orderId: number,
  status: "Settled" | "Failed"
): Promise<Order> {
  const res = await fetch(`${API_BASE}/api/orders/${orderId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const text = await res.text();
    let message = `Failed to update order: ${res.status} ${res.statusText}`;
    try {
      const j = JSON.parse(text);
      if (j.detail) message = j.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  return res.json();
}
