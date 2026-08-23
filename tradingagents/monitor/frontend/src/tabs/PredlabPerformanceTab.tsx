import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { EquityChart } from "../charts/EquityChart";
import { fmtBps, fmtNum, fmtPct, fmtUsd, fmtWarmup } from "../lib/format";
import { rebaseTo100, sliceFromDays } from "../lib/rebase";
import { safeAccount, safeNav } from "../lib/predlabGuard";
import type {
  PredlabBookPerf, PredlabYearlyRow, PredlabNav, PredlabAccount, Point,
} from "../types";

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

/** NAV / account series are already base-100 — slice+rebase to the
 *  selected range the same way the raw book equity is. */
function prepSeries(series: Point[] | undefined, days: number | null): Point[] {
  return series ? rebaseTo100(sliceFromDays(series, days)) : [];
}

function CardsRow(props: {
  name: string; kind: "quant" | "hybrid"; p: PredlabBookPerf;
  nav: PredlabNav | null;
}) {
  const c = props.p.cards;
  const slip = props.p.slippage;
  const warm = c.warmup.n < c.warmup.required;
  const nav = props.nav;
  const navActive = !!nav && nav.cards.active_days > 0;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={props.kind}>{props.name.toUpperCase()}</Badge>{" "}
      <span className="muted">as of {c.last_asof} · {c.n_days} rows</span>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Book return (gross 2x, unscaled)" value={fmtPct(c.cum_return)}
          tone={c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Account NAV (scaled)"
          value={navActive ? fmtPct(nav!.cards.nav_cum_return)
            : fmtWarmup(nav?.cards.warmup.n ?? 0, nav?.cards.warmup.required ?? 21)}
          tone={navActive && nav!.cards.nav_cum_return !== null
            ? (nav!.cards.nav_cum_return >= 0 ? "pos" : "neg") : ""} />
        <Card label="Sharpe (paper)" value={fmtNum(c.sharpe)}
          tone={c.sharpe >= 0 ? "pos" : "neg"} />
        <Card label="Max drawdown" value={fmtPct(c.max_drawdown)} tone="neg" />
        <Card label="VT scale"
          value={c.scale !== null ? fmtNum(c.scale)
            : `warming up (${c.warmup.n}/${c.warmup.required})`} />
        <Card label="Avg turnover" value={fmtPct(c.avg_turnover)} />
        <Card label="Cum est. cost" value={fmtPct(c.cum_cost)} tone="neg" />
        <Card label="Fill slippage (mark vs close)"
          value={slip ? `${fmtBps(slip.mean_bps)}/day` : "accruing"}
          tone={slip ? (slip.mean_bps >= 0 ? "pos" : "neg") : ""} />
      </div>
      {nav && nav.cards.last_scale !== null && <p className="muted">
        last overlay scale applied to the account: {fmtNum(nav.cards.last_scale)}</p>}
      {warm && <p className="muted">
        vol-target scale needs {c.warmup.required} realized returns —
        {" "}{c.warmup.required - c.warmup.n} to go</p>}
      {slip
        ? <p className="muted">
            fill check over {slip.n} paired day{slip.n === 1 ? "" : "s"}:
            {" "}{fmtBps(slip.cum_bps)} cumulative · last {slip.last.asof}
            {" "}close {fmtPct(slip.last.close_ret)} vs mark
            {" "}{fmtPct(slip.last.mark_ret)} ({fmtBps(slip.last.bps)})</p>
        : <p className="muted">
            fill check accruing — rows carry write-time marks from
            {" "}2026-08-18; the first paired day needs two marked rows</p>}
    </div>
  );
}

function AccountCardsRow(props: { venue: string; a: PredlabAccount }) {
  const c = props.a.cards;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={c.halted ? "error" : "ok"}>{props.venue.toUpperCase()}</Badge>{" "}
      {c.halted && <Badge kind="error">HALTED</Badge>}{" "}
      <span className="muted">
        as of {c.last_asof}{c.dry_run_last ? " (dry-run)" : ""}
        {" "}· {c.n_cycles} cycles</span>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Account cumulative return" value={fmtPct(c.cum_return)}
          tone={c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Equity" value={fmtUsd(c.equity)} />
        <Card label="Cycles" value={fmtNum(c.n_cycles, 0)} />
        <Card label="Orders placed (total)" value={fmtNum(c.orders_total, 0)} />
      </div>
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
  const champNav = useMemo(
    () => prepSeries(safeNav(d, "champion")?.series, days), [d, days]);
  const vt10Nav = useMemo(
    () => prepSeries(safeNav(d, "vt10")?.series, days), [d, days]);
  const testnetAcct = useMemo(
    () => prepSeries(safeAccount(d, "testnet")?.series, days), [d, days]);
  const liveAcct = useMemo(
    () => prepSeries(safeAccount(d, "live")?.series, days), [d, days]);
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !d) return <div className="badge error">failed: {String(q.error)}</div>;

  const navChampion = safeNav(d, "champion");
  const navVt10 = safeNav(d, "vt10");
  const acctTestnet = safeAccount(d, "testnet");
  const acctLive = safeAccount(d, "live");

  const extraEquity = [
    navChampion && { label: "champion NAV", color: "#d29922", data: champNav },
    navVt10 && { label: "vt10 NAV", color: "#56d4dd", data: vt10Nav },
    acctTestnet && { label: "testnet account", color: "#58a6ff", data: testnetAcct },
    acctLive && { label: "live account", color: "#f85149", data: liveAcct },
  ].filter((x): x is { label: string; color: string; data: typeof champNav } => !!x);

  return (
    <>
      {d.books.champion
        ? <CardsRow name="champion" kind="quant" p={d.books.champion}
            nav={navChampion} />
        : <p className="muted">champion journal unavailable</p>}
      {d.books.vt10
        ? <CardsRow name="vt10 (old book)" kind="hybrid" p={d.books.vt10}
            nav={navVt10} />
        : <p className="muted">vt10 journal unavailable</p>}

      {acctTestnet && <AccountCardsRow venue="testnet" a={acctTestnet} />}
      {acctLive && <AccountCardsRow venue="live" a={acctLive} />}

      <Section title="Paper equity + NAV/account (indexed to 100) · drawdown · rolling Sharpe"
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
          extraEquity={extraEquity}
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
