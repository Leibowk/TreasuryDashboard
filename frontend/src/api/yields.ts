const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface YieldPoint {
  term: string;
  rate: number;
}

export interface YieldCurveResponse {
  data: YieldPoint[];
}

export async function fetchYieldCurve(date: string): Promise<YieldCurveResponse> {
  const url = `${API_BASE}/api/yields?date=${encodeURIComponent(date)}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load yields: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
