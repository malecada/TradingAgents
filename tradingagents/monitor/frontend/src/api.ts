import type {
  CycleDetail, CycleRow, HealthResp, PerformanceResp, PositionsResp,
  Strategy, TradesResp,
  AdhocMeta, AdhocRunBody, AdhocStatus, AdhocResult, AdhocRunRow,
  PredlabBookName, PredlabPerformanceResp, PredlabBookResp, PredlabGateResp, PredlabHealthResp,
} from "./types";

/** Thin fetch wrapper. Browser basic-auth (401 challenge) covers credentials. */
async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  performance: () => get<PerformanceResp>("/api/performance"),
  positions: () => get<PositionsResp>("/api/positions"),
  trades: (s: Strategy) => get<TradesResp>(`/api/trades?strategy=${s}`),
  cycles: (s: Strategy) => get<{ cycles: CycleRow[] }>(`/api/cycles?strategy=${s}`),
  cycle: (id: string, s: Strategy) =>
    get<CycleDetail>(`/api/cycle/${encodeURIComponent(id)}?strategy=${s}`),
  health: () => get<HealthResp>("/api/health"),
  adhocMeta: () => get<AdhocMeta>("/api/adhoc/meta"),
  adhocRun: (body: AdhocRunBody) => post<{ run_id: string }>("/api/adhoc/run", body),
  adhocStatus: (id: string) =>
    get<AdhocStatus>(`/api/adhoc/status/${encodeURIComponent(id)}`),
  adhocResult: (id: string) =>
    get<AdhocResult>(`/api/adhoc/result/${encodeURIComponent(id)}`),
  adhocRuns: () => get<{ runs: AdhocRunRow[] }>("/api/adhoc/runs"),
  predlabPerformance: () =>
    get<PredlabPerformanceResp>("/api/predlab/performance"),
  predlabBook: (b: PredlabBookName) =>
    get<PredlabBookResp>(`/api/predlab/book?book=${b}`),
  predlabGate: () => get<PredlabGateResp>("/api/predlab/gate"),
  predlabHealth: () => get<PredlabHealthResp>("/api/predlab/health"),
};
