import { useCallback, useEffect, useRef, useState } from "react";
import {
  createOrder,
  fetchOrders,
  updateOrderStatus,
  type Order,
} from "./api/orders";
import { fetchYieldCurve, type YieldPoint } from "./api/yields";
import { YieldCurveChart } from "./components/YieldCurveChart";

const TERM_OPTIONS = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"];
const PAGE_SIZE_OPTIONS = [5, 10, 25, 50, 100];

/** Format date as YYYY-MM-DD in the user's local timezone (not UTC). */
function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function today(): string {
  return formatDate(new Date());
}

function formatDisplayDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-");
  return `${m}/${d}/${y}`;
}

export default function App() {
  const [selectedDate, setSelectedDate] = useState(today);
  const [data, setData] = useState<YieldPoint[] | null>(null);
  const [displayDate, setDisplayDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [ordersOffset, setOrdersOffset] = useState(0);
  const [ordersPageSize, setOrdersPageSize] = useState(10);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createTerm, setCreateTerm] = useState("5Y");
  const [createAmount, setCreateAmount] = useState("");
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const scrollRestoreRef = useRef<number | null>(null);

  const loadYields = useCallback(async (date: string) => {
    setLoading(true);
    setError(null);
    setDisplayDate(null);
    try {
      const res = await fetchYieldCurve(date);
      setData(res.data);
      setDisplayDate(res.display_date);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load yield curve");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadYields(selectedDate);
  }, [selectedDate, loadYields]);

  const loadOrders = useCallback(
    async (offset: number = ordersOffset, limit: number = ordersPageSize) => {
      setOrdersLoading(true);
      setOrdersError(null);
      const savedY = scrollRestoreRef.current;
      if (savedY !== null) {
        requestAnimationFrame(() => window.scrollTo(0, savedY));
      }
      try {
        const res = await fetchOrders(offset, limit);
        setOrders(res.orders);
        setOrdersTotal(res.total);
      } catch (e) {
        setOrdersError(
          e instanceof Error ? e.message : "Failed to load orders"
        );
        setOrders([]);
        setOrdersTotal(0);
      } finally {
        setOrdersLoading(false);
      }
    },
    [ordersOffset, ordersPageSize]
  );

  useEffect(() => {
    loadOrders(ordersOffset, ordersPageSize);
  }, [ordersOffset, ordersPageSize, loadOrders]);

  useEffect(() => {
    if (!ordersLoading && scrollRestoreRef.current !== null) {
      const y = scrollRestoreRef.current;
      scrollRestoreRef.current = null;
      requestAnimationFrame(() => window.scrollTo(0, y));
    }
  }, [ordersLoading]);

  const saveScrollAnd = (fn: () => void) => {
    scrollRestoreRef.current = window.scrollY;
    fn();
  };

  const handlePageSizeChange = (newSize: number) => {
    saveScrollAnd(() => {
      setOrdersPageSize(newSize);
      setOrdersOffset(0);
    });
  };

  const goToPrevPage = () => {
    saveScrollAnd(() => setOrdersOffset((o) => Math.max(0, o - ordersPageSize)));
  };

  const goToNextPage = () => {
    saveScrollAnd(() => setOrdersOffset((o) => o + ordersPageSize));
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amount = parseFloat(createAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setCreateError("Please enter a valid positive amount.");
      return;
    }
    setCreateSubmitting(true);
    setCreateError(null);
    try {
      await createOrder(createTerm, amount);
      setCreateOpen(false);
      setCreateAmount("");
      setCreateTerm("5Y");
      scrollRestoreRef.current = window.scrollY;
      loadOrders();
    } catch (e) {
      setCreateError(
        e instanceof Error ? e.message : "Failed to create order"
      );
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleStatusUpdate = async (orderId: number, status: "Settled" | "Failed") => {
    scrollRestoreRef.current = window.scrollY;
    setActionLoadingId(orderId);
    try {
      await updateOrderStatus(orderId, status);
      loadOrders();
    } finally {
      setActionLoadingId(null);
    }
  };

  const formatOrderDate = (iso: string) => {
    const [y, m, d] = iso.split("-");
    return `${m}/${d}/${y}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900 sm:text-3xl">
          Treasury Yields
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Yield curve by term. Select a date to refresh.
        </p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <label htmlFor="yield-date" className="text-sm font-medium text-gray-700">
            As of date
          </label>
          <input
            id="yield-date"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          />
        </div>

        <div className="mt-8 rounded-lg border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
          {error && (
            <div
              className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}
          {loading && (
            <div className="flex h-[360px] items-center justify-center text-gray-500">
              Loading…
            </div>
          )}
          {!loading && data && data.length > 0 && (
            <YieldCurveChart data={data} />
          )}
          {!loading && data && data.length === 0 && !error && (
            <div className="flex h-[360px] items-center justify-center text-gray-500">
              No data for this date.
            </div>
          )}
        </div>

        {!loading && displayDate && displayDate !== selectedDate && (
          <p className="mt-6 text-center text-sm text-amber-700" role="status">
            Data for the selected date has not been released yet. Currently
            displaying {formatDisplayDate(displayDate)} data.
          </p>
        )}

        <section className="mt-12">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-gray-900">
              Order History
            </h2>
            <button
              type="button"
              onClick={() => {
                setCreateOpen(true);
                setCreateError(null);
              }}
              className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2"
            >
              Create Order
            </button>
          </div>

          {createOpen && (
            <div
              className="fixed inset-0 z-10 flex items-center justify-center bg-black/40"
              role="dialog"
              aria-modal="true"
              aria-labelledby="create-order-title"
            >
              <div className="mx-4 w-full max-w-sm rounded-lg border border-gray-200 bg-white p-6 shadow-lg">
                <h3 id="create-order-title" className="text-lg font-semibold text-gray-900">
                  Create Order
                </h3>
                <form onSubmit={handleCreateSubmit} className="mt-4 space-y-4">
                  {createError && (
                    <div
                      className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                      role="alert"
                    >
                      {createError}
                    </div>
                  )}
                  <div>
                    <label htmlFor="create-term" className="block text-sm font-medium text-gray-700">
                      Term
                    </label>
                    <select
                      id="create-term"
                      value={createTerm}
                      onChange={(e) => setCreateTerm(e.target.value)}
                      className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
                    >
                      {TERM_OPTIONS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="create-amount" className="block text-sm font-medium text-gray-700">
                      Amount ($)
                    </label>
                    <input
                      id="create-amount"
                      type="number"
                      min="0.01"
                      step="any"
                      required
                      value={createAmount}
                      onChange={(e) => setCreateAmount(e.target.value)}
                      className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setCreateOpen(false);
                        setCreateError(null);
                      }}
                      className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createSubmitting}
                      className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                    >
                      {createSubmitting ? "Submitting…" : "Submit"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-4">
            <label htmlFor="orders-page-size" className="text-sm font-medium text-gray-700">
              Show
            </label>
            <select
              id="orders-page-size"
              value={ordersPageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm shadow-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            >
              {PAGE_SIZE_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <span className="text-sm text-gray-600">per page</span>
          </div>

          <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            {ordersError && (
              <div
                className="border-b border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                role="alert"
              >
                {ordersError}
              </div>
            )}
            <div
              className={`overflow-x-auto transition-opacity duration-150 ${ordersLoading ? "opacity-70" : "opacity-100"}`}
              aria-busy={ordersLoading}
            >
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Term
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Amount $
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Yield %
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Status
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {ordersLoading && orders.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                        Loading orders…
                      </td>
                    </tr>
                  ) : orders.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                        No orders yet. Create one to get started.
                      </td>
                    </tr>
                  ) : (
                    orders.map((order) => (
                        <tr key={order.id}>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                            {formatOrderDate(order.date)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                            {order.term}
                          </td>
                          <td
                            className={
                              "whitespace-nowrap px-4 py-3 text-sm font-semibold " +
                              (order.amount < 0 ? "text-red-600" : "text-gray-900")
                            }
                          >
                            {order.amount >= 0 ? "+" : ""}$
                            {order.amount.toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                            {order.yield_pct.toFixed(2)}%
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm">
                            <span
                              className={
                                order.status === "Pending"
                                  ? "inline-flex rounded-full border border-amber-700/30 bg-[#fff3cd] px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-[#8a6d3b]"
                                  : order.status === "Settled"
                                    ? "inline-flex rounded-full border border-green-700/20 bg-[#d1eddb] px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-[#3c763d]"
                                    : "inline-flex rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-red-800"
                              }
                            >
                              {order.status}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                            {order.status === "Pending" ? (
                              <span className="inline-flex gap-2">
                                <button
                                  type="button"
                                  disabled={actionLoadingId === order.id}
                                  onClick={() => handleStatusUpdate(order.id, "Settled")}
                                  className="rounded-md bg-[#28a745] px-3 py-1.5 font-semibold text-white shadow-sm hover:bg-[#218838] disabled:opacity-50"
                                >
                                  {actionLoadingId === order.id ? "…" : "Settle"}
                                </button>
                                <button
                                  type="button"
                                  disabled={actionLoadingId === order.id}
                                  onClick={() => handleStatusUpdate(order.id, "Failed")}
                                  className="rounded-md border border-red-200 bg-red-50 px-3 py-1.5 font-semibold text-red-800 hover:bg-red-100 disabled:opacity-50"
                                >
                                  Fail
                                </button>
                              </span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </td>
                        </tr>
                      ))
                  )}
                </tbody>
              </table>
            </div>
            {ordersTotal > 0 && (
              <div className="flex flex-wrap items-center justify-between gap-4 border-t border-gray-200 bg-gray-50 px-4 py-3 text-sm">
                <span className="text-gray-600">
                  Showing {ordersOffset + 1}–
                  {Math.min(ordersOffset + ordersPageSize, ordersTotal)} of {ordersTotal}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={ordersOffset === 0}
                    onClick={goToPrevPage}
                    className="rounded-md border border-gray-300 bg-white px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50 disabled:pointer-events-none disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={ordersOffset + ordersPageSize >= ordersTotal}
                    onClick={goToNextPage}
                    className="rounded-md border border-gray-300 bg-white px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50 disabled:pointer-events-none disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
