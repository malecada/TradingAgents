import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { pollInterval } from "../lib/adhoc";
import { fmtNum } from "../lib/format";
import type { AdhocOutput, AdhocStrategy } from "../types";

/** Pull the 5-level rating out of the portfolio-manager prose for the headline
 *  card (the full reasoning stays in the collapsible "Portfolio manager" panel). */
function shortRating(text: unknown): string | null {
  if (typeof text !== "string") return null;
  const m = text.toUpperCase().match(/\b(BUY|OVERWEIGHT|HOLD|UNDERWEIGHT|SELL)\b/g);
  return m ? m[m.length - 1] : null;  // last mention = the conclusion
}

function Panel(props: { o: AdhocOutput }) {
  const { o } = props;
  return (
    <details style={{ marginBottom: 8 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>{o.label}</summary>
      {o.kind === "json" ? (
        <pre style={{ whiteSpace: "pre-wrap", background: "#161b22",
                      border: "1px solid #30363d", borderRadius: 6, padding: 12,
                      marginTop: 8, overflowX: "auto" }}>
          {JSON.stringify(o.content, null, 2)}
        </pre>
      ) : (
        <div className="md" style={{ background: "#161b22", border: "1px solid #30363d",
                                     borderRadius: 6, padding: "2px 14px", marginTop: 8 }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(o.content ?? "")}</ReactMarkdown>
        </div>
      )}
    </details>
  );
}

const ANALYST_OPTIONS = ["market", "onchain", "prediction", "crypto_sentiment"] as const;

export function RunTab() {
  const [coin, setCoin] = useState("bitcoin");
  const [date, setDate] = useState("");
  const [strategy, setStrategy] = useState<AdhocStrategy>("quant");
  const [model, setModel] = useState("gpt-4o-mini");
  const [analysts, setAnalysts] = useState<string[]>(["market", "onchain", "prediction"]);
  const [runId, setRunId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Poll meta faster while a run is in flight so `job_running` clears promptly
  // when the worker finishes (else the Run button stays disabled up to 30s).
  const metaQ = useQuery({
    queryKey: ["adhocMeta"], queryFn: api.adhocMeta,
    refetchInterval: runId ? 3_000 : 30_000,
  });
  const meta = metaQ.data;

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
          `Hybrid run (${analysts.length} analysts, ${model}) hits live Binance + LLM APIs and takes ~90–120s. Continue?`)) return;
    try {
      const body = strategy === "hybrid"
        ? { coin, date, strategy, analysts, model }
        : { coin, date, strategy };
      const { run_id } = await api.adhocRun(body);
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
          {strategy === "hybrid" && (
            <select value={model} onChange={(e) => setModel(e.target.value)}
              style={{ background: "#161b22", color: "#e6edf3",
                       border: "1px solid #30363d", borderRadius: 6, padding: "4px 8px" }}>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
            </select>
          )}
          <button className="run-btn" disabled={busy || meta?.job_running}
            onClick={start}>{busy ? "running…" : "▸ Run prediction"}</button>
          {meta?.job_running && !runId &&
            <Badge kind="stale">another job is running</Badge>}
        </div>
        {err && <p style={{ color: "#f85149" }}>{err}</p>}
        {strategy === "hybrid" && (
          <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
            {ANALYST_OPTIONS.map((a) => (
              <label key={a} style={{ display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
                <input type="checkbox" checked={analysts.includes(a)}
                  onChange={(e) => setAnalysts(e.target.checked
                    ? [...analysts, a]
                    : analysts.filter((x) => x !== a))} />
                {a}
              </label>
            ))}
            <span className="muted">sentiment omitted by default for BTC/ETH</span>
          </div>
        )}
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

      {status?.status === "done" && resultQ.data && (
        <>
          <Section title="Final decision">
            <div className="cards">
              <Card label={finalObj.strategy === "hybrid" ? "Rating" : "Direction"}
                value={String(finalObj.direction ?? shortRating(finalObj.pm) ?? "—")} />
              {"magnitude" in finalObj &&
                <Card label="Magnitude" value={fmtNum(Number(finalObj.magnitude), 3)} />}
              {"multiplier" in finalObj &&
                <Card label="LLM multiplier" value={fmtNum(Number(finalObj.multiplier), 3)} />}
              {"effective_weight" in finalObj &&
                <Card label="Effective weight" value={fmtNum(Number(finalObj.effective_weight), 3)} />}
              {finalObj.regime != null &&
                <Card label="Regime" value={String(finalObj.regime)} />}
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
