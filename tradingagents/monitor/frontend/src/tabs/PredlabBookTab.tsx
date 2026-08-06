import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { fmtNum, fmtPct } from "../lib/format";
import type { PredlabBookName, PredlabWeight } from "../types";

const BOOKS: PredlabBookName[] = ["champion", "vt10"];

function WeightsTable(props: { title: string; rows: PredlabWeight[] }) {
  return (
    <div style={{ flex: 1, minWidth: 260 }}>
      <h3>{props.title} ({props.rows.length})</h3>
      <table>
        <thead><tr><th>Symbol</th><th>Weight</th></tr></thead>
        <tbody>
          {props.rows.map((r) => (
            <tr key={r.symbol}><td>{r.symbol}</td>
              <td>{fmtPct(r.weight)}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PredlabBookTab() {
  const [book, setBook] = useState<PredlabBookName>("champion");
  const q = useQuery({
    queryKey: ["predlab-book", book], queryFn: () => api.predlabBook(book),
  });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const d = q.data.detail;

  return (
    <>
      <div className="pills" style={{ marginTop: 10 }}>
        {BOOKS.map((b) => (
          <button key={b} className={`pill ${b === book ? "active" : ""}`}
            onClick={() => setBook(b)}>{b}</button>
        ))}
      </div>
      {!d ? <p className="muted">no journal rows for {book}</p> : (
        <>
          <div className="cards" style={{ marginTop: 10 }}>
            <Card label="As of" value={d.asof} />
            <Card label="Universe" value={String(d.n_universe ?? "—")} />
            <Card label="Breadth" value={String(d.breadth ?? "—")} />
            <Card label="VT scale" value={fmtNum(d.scale)} />
            <Card label="Est. turnover" value={fmtPct(d.est_turnover)} />
            <Card label="Est. cost" value={fmtPct(d.est_cost)} />
          </div>
          <p className="muted">
            membership {d.membership_hash ?? "—"}
            {d.delta && <> · vs prev day: {d.delta.entered} entered,
              {" "}{d.delta.exited} exited</>}
          </p>
          <Section title="Today's book">
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              <WeightsTable title="Long" rows={d.longs} />
              <WeightsTable title="Short" rows={d.shorts} />
            </div>
          </Section>
        </>
      )}
    </>
  );
}
