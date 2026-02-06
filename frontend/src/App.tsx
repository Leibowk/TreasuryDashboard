import { useCallback, useEffect, useState } from "react";
import { fetchYieldCurve, type YieldPoint } from "./api/yields";
import { YieldCurveChart } from "./components/YieldCurveChart";

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
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
      </main>
    </div>
  );
}
