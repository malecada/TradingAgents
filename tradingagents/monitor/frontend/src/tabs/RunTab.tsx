import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { pollInterval } from "../lib/adhoc";
import type { AdhocOutput, AdhocStrategy } from "../types";

function Panel(props: { o: AdhocOutput }) {
  const { o } = props;
  const text = o.kind === "json"
    ? JSON.stringify(o.content, null, 2)
    : String(o.content ?? "");
  return (
    <details style={{ marginBottom: 8 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>{o.label}</summary>
      <pre style={{ whiteSpace: "pre-wrap", background: "#161b22",
                    border: "1px solid #30363d", borderRadius: 6, padding: 12,
                    marginTop: 8, overflowX: "auto" }}>{text}</pre>
    </details>
  );
}

export function RunTab() {
  const metaQ = useQuery({ queryKey: ["adhocMeta"], queryFn: api.adhocMeta });
  const meta = metaQ.data;

  const [coin, setCoin] = useState("bitcoin");
  const [date, setDate] = useState("");
  const [strategy, setStrategy] = useState<AdhocStrategy>("quant");
  const [runId, setRunId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const statusQ = useQuery({
    queryKey: ["adhocStatus", runId],
    queryFn: () => api.adhocStatus(runId!),
    enabled: runId !== null,
    refetchInterval: (query) => pollInterval(query.state.data?.status),
  });
  const status = statusQ.data;

  const resultQ = useQuery({
    queryKey: ["adhocResult", runId],
    queryFn: () => api.adhocResult(runId!),
    enabled: runId !== null && status?.status === "done",
  });

  const runsQ = useQuery({ queryKey: ["adhocRuns"], queryFn: api.adhocRuns,
                           refetchInterval: 10_000 });

  async function start() {
    setErr(null);
    if (!date) { setErr("pick a date"); return; }
    if (strategy === "hybrid" &&
        !window.confirm(
          "Hybrid run hits live Binance + LLM APIs and takes ~90–120s " +
          "(est. cost ~$0.002, gpt-4o-mini). Continue?")) return;
    try {
      const { run_id } = await api.adhocRun({ coin, date, strategy });
      setRunId(run_id);
    } catch (e) {
      setErr(String(e));
    }
  }

  const outputs = resultQ.data?.outputs ?? [];
  const final = outputs.find((o) => o.key === "final");
  const finalObj = (final?.content ?? {}) as Record<string, unknown>;
  const busy = status?.status === "queued" || status?.status === "running";

  return (
    <>
      <Section title="Run an ad-hoc prediction">
        <div className="pills" style={{ gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <select value={coin} onChange={(e) => setCoin(e.target.value)}
            style={{ background: "#161b22", color: "#e6edf3",
                     border: "1px solid #30363d", borderRadius: 6, padding: "4px 8px" }}>
            {(meta?.coins ?? ["bitcoin"]).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
            style={{ background: "#161b22", color: "#e6edf3",
                     border: "1px solid #30363d", borderRadius: 6, padding: "4px 8px" }} />
          {(["quant", "hybrid"] as AdhocStrategy[]).map((s) => (
            <button key={s} className={`pill ${s === strategy ? "active" : ""}`}
              onClick={() => setStrategy(s)}>{s}</button>
          ))}
          <button className="pill active" disabled={busy || meta?.job_running}
            onClick={start}>{busy ? "running…" : "Run"}</button>
          {meta?.job_running && !runId &&
            <Badge kind="stale">another job is running</Badge>}
        </div>
        {err && <p style={{ color: "#f85149" }}>{err}</p>}
        <p className="muted" style={{ marginTop: 8 }}>
          Historical dates use the latest model checkpoint (features are
          point-in-time; model weights are as-of-latest). Display only — no trade
          is placed.
        </p>
      </Section>

      {status && (
        <Section title="Progress" right={
          <Badge kind={status.status === "error" ? "error"
            : status.status === "done" ? "ok" : "stale"}>{status.status}</Badge>}>
          <p>{status.stage ?? "…"}{status.error_msg ? ` — ${status.error_msg}` : ""}</p>
        </Section>
      )}

      {status?.status === "done" && (
        <>
          <Section title="Final decision">
            <div className="cards">
              <Card label="Direction" value={String(finalObj.direction ?? finalObj.pm ?? "—")} />
              {"magnitude" in finalObj &&
                <Card label="Magnitude" value={String(finalObj.magnitude)} />}
              {"multiplier" in finalObj &&
                <Card label="LLM multiplier" value={String(finalObj.multiplier)} />}
              {"effective_weight" in finalObj &&
                <Card label="Effective weight" value={String(finalObj.effective_weight)} />}
              {"regime" in finalObj && <Card label="Regime" value={String(finalObj.regime)} />}
            </div>
            <button className="pill" disabled title="coming soon"
              style={{ marginTop: 12, opacity: 0.5 }}>Trade this prediction</button>
          </Section>

          <Section title="Agent & partial outputs">
            {outputs.filter((o) => o.key !== "final").map((o) => <Panel key={o.ordinal} o={o} />)}
          </Section>
        </>
      )}

      <Section title="Recent runs">
        <table>
          <thead><tr><th>When</th><th>Coin</th><th>Strategy</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {(runsQ.data?.runs ?? []).map((r) => (
              <tr key={r.run_id}>
                <td>{new Date(r.created_ts * 1000).toLocaleString()}</td>
                <td>{r.coin}</td><td>{r.strategy}</td><td>{r.status}</td>
                <td><button className="pill" onClick={() => setRunId(r.run_id)}>view</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  );
}
