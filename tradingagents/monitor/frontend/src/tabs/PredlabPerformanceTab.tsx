import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { EquityChart } from "../charts/EquityChart";
import { fmtNum, fmtPct } from "../lib/format";
import { rebaseTo100, sliceFromDays } from "../lib/rebase";
import type { PredlabBookPerf, PredlabYearlyRow } from "../types";

const RANGES = [
  { label: "7d", days: 7 }, { label: "30d", days: 30 },
  { label: "90d", days: 90 }, { label: "all", days: null },
] as const;

function prep(p: PredlabBookPerf | null, days: number | null) {
  return {
    eq: p ? rebaseTo100(sliceFromDays(p.equity, days)) : [],
    dd: p ? sliceFromDays(p.drawdown, days) : [],
    rs: p ? sliceFromDays(p.rolling_sharpe, days) : [],
  };
}

function CardsRow(props: {
  name: string; kind: "quant" | "hybrid"; p: PredlabBookPerf;
}) {
  const c = props.p.cards;
  const warm = c.warmup.n < c.warmup.required;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={props.kind}>{props.name.toUpperCase()}</Badge>{" "}
      <span className="muted">as of {c.last_asof} · {c.n_days} rows</span>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Cumulative return" value={fmtPct(c.cum_return)}
          tone={c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Sharpe (paper)" value={fmtNum(c.sharpe)}
          tone={c.sharpe >= 0 ? "pos" : "neg"} />
        <Card label="Max drawdown" value={fmtPct(c.max_drawdown)} tone="neg" />
        <Card label="VT scale"
          value={c.scale !== null ? fmtNum(c.scale)
            : `warming up (${c.warmup.n}/${c.warmup.required})`} />
        <Card label="Avg turnover" value={fmtPct(c.avg_turnover)} />
        <Card label="Cum est. cost" value={fmtPct(c.cum_cost)} tone="neg" />
      </div>
      {warm && <p className="muted">
        vol-target scale needs {c.warmup.required} realized returns —
        {" "}{c.warmup.required - c.warmup.n} to go</p>}
    </div>
  );
}

function YearlyTable(props: {
  years: Record<string, PredlabYearlyRow>; title: string;
}) {
  const keys = Object.keys(props.years).sort();
  return (
    <table>
      <thead><tr><th>{props.title}</th><th>SR</th><th>Return</th>
        <th>Max DD</th><th>Days</th></tr></thead>
      <tbody>
        {keys.map((y) => (
          <tr key={y}><td>{y}</td>
            <td>{fmtNum(props.years[y].sr)}</td>
            <td>{fmtPct(props.years[y].ret)}</td>
            <td>{fmtPct(props.years[y].maxdd)}</td>
            <td>{props.years[y].n_days}</td></tr>
        ))}
      </tbody>
    </table>
  );
}

export function PredlabPerformanceTab() {
  const q = useQuery({
    queryKey: ["predlab-performance"], queryFn: api.predlabPerformance,
  });
  const [days, setDays] = useState<number | null>(null);
  const d = q.data;
  const champ = useMemo(() => prep(d?.books.champion ?? null, days), [d, days]);
  const vt10 = useMemo(() => prep(d?.books.vt10 ?? null, days), [d, days]);
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !d) return <div className="badge error">failed: {String(q.error)}</div>;

  return (
    <>
      {d.books.champion
        ? <CardsRow name="champion" kind="quant" p={d.books.champion} />
        : <p className="muted">champion journal unavailable</p>}
      {d.books.vt10
        ? <CardsRow name="vt10 (old book)" kind="hybrid" p={d.books.vt10} />
        : <p className="muted">vt10 journal unavailable</p>}

      <Section title="Paper equity (indexed to 100) · drawdown · rolling Sharpe"
        right={
          <div className="pills">
            {RANGES.map((r) => (
              <button key={r.label} className={`pill ${days === r.days ? "active" : ""}`}
                onClick={() => setDays(r.days)}>{r.label}</button>
            ))}
          </div>
        }>
        <EquityChart
          quantEquity={champ.eq} hybridEquity={vt10.eq}
          quantDd={champ.dd} hybridDd={vt10.dd}
          quantRs={champ.rs} hybridRs={vt10.rs}
          anchors={{ quant: d.reference?.ovl_sr_full ?? 0, hybrid: null }}
          labels={{ a: "champion", b: "vt10" }}
        />
        {(d.books.champion?.rolling_sharpe.length ?? 0) === 0 &&
          <p className="muted">rolling Sharpe appears after 30 realized days</p>}
      </Section>

      {d.reference && (
        <Section title="Frozen dev reference (2021-01 → 2026-07, backtest)">
          <div className="cards">
            <Card label="Overlaid SR" value={fmtNum(d.reference.ovl_sr_full)} />
            <Card label="Overlaid MaxDD" value={fmtPct(d.reference.ovl_maxdd)} tone="neg" />
            <Card label="Raw SR" value={fmtNum(d.reference.raw_sr_full)} />
            <Card label="DSR (selection pool)" value={fmtNum(d.reference.dsr_selection_pool)} />
          </div>
        </Section>
      )}

      {d.backtest_yearly?.champion && (
        <Section title="Backtest (dev) yearly — overlaid, net">
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <YearlyTable years={d.backtest_yearly.champion} title="champion" />
            {d.backtest_yearly.vt10 &&
              <YearlyTable years={d.backtest_yearly.vt10} title="vt10" />}
          </div>
        </Section>
      )}
    </>
  );
}
