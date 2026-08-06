import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { fmtNum } from "../lib/format";

export function PredlabGateTab() {
  const q = useQuery({ queryKey: ["predlab-gate"], queryFn: api.predlabGate });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const g = q.data;
  const total = g.days_elapsed + g.days_remaining;
  const pct = total > 0 ? Math.min(100, (g.days_elapsed / total) * 100) : 0;

  return (
    <>
      <p className="muted" style={{ marginTop: 10 }}>
        Informational tracker only — the forward evaluation is ONE-SHOT,
        earliest {g.earliest_eval}. Nothing shown here constitutes an
        evaluation of the sealed window.
      </p>
      <div className="cards">
        <Card label="Forward window start" value={g.window_start} />
        <Card label="Earliest evaluation" value={g.earliest_eval} />
        <Card label="Days elapsed" value={String(g.days_elapsed)} />
        <Card label="Days remaining" value={String(g.days_remaining)} />
        <Card label="Threshold SR" value={fmtNum(g.threshold_sr, 3)} />
        <Card label="Running SR (paper proxy)"
          value={g.running.sr === null
            ? `— (${g.running.n_returns} returns)` : fmtNum(g.running.sr)}
          tone={(g.running.sr ?? 0) >= g.threshold_sr ? "pos" : ""} />
      </div>
      <Section title={`Progress to earliest evaluation (${pct.toFixed(0)}%)`}>
        <div style={{ background: "#21262d", borderRadius: 4, height: 14 }}>
          <div style={{
            width: `${pct}%`, height: "100%", borderRadius: 4,
            background: "#3fb950",
          }} />
        </div>
      </Section>
      <Section title="Pass criteria (sealed one-shot)">
        <ul>{g.criteria.map((c) => <li key={c}>{c}</li>)}</ul>
        <p className="muted">{g.running.note}</p>
      </Section>
    </>
  );
}
