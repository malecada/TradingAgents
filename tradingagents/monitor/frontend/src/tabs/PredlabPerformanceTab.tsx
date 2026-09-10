import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { EquityChart } from "../charts/EquityChart";
import { fmtBps, fmtNum, fmtPct, fmtUsd, fmtWarmup } from "../lib/format";
import { rebaseTo100, sliceFromDays } from "../lib/rebase";
import { correctedPayload, safeAccount, safeNav } from "../lib/predlabGuard";
import type {
  PredlabBookPerf, PredlabNav, PredlabAccount, Point,
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
  const eligible = props.p.measurement_status === 'corrected_v2' || props.p.measurement_status === 'warmup';
  const warm = eligible && c.warmup.n < c.warmup.required;
  const nav = props.nav;
  const navActive = !!nav && nav.cards.nav_cum_return !== null;
  const navWarming = nav?.measurement_status === 'warmup';
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={props.kind}>{props.name.toUpperCase()}</Badge>{" "}
      <span className="muted">as of {c.last_asof} · {c.n_days} dates</span>
      <p>Base measurement: {props.p.measurement_status ?? 'unavailable'}
        {props.p.measurement_reason && <> · {props.p.measurement_reason}</>}</p>
      <p>Overlay measurement: {nav?.measurement_status ?? 'unavailable'}
        {nav?.measurement_reason && <> · {nav.measurement_reason}</>}</p>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Base book return (net)" value={fmtPct(c.cum_return)}
          tone={c.cum_return === null ? "" : c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Paper overlay return (net)"
          value={navActive ? fmtPct(nav!.cards.nav_cum_return)
            : navWarming ? fmtWarmup(nav?.cards.warmup.n ?? 0, nav?.cards.warmup.required ?? 20) : "Unavailable"}
          tone={navActive && nav!.cards.nav_cum_return !== null
            ? (nav!.cards.nav_cum_return >= 0 ? "pos" : "neg") : ""} />
        <Card label="Sharpe (base net)" value={fmtNum(c.sharpe)}
          tone={c.sharpe === null ? "" : c.sharpe >= 0 ? "pos" : "neg"} />
        <Card label="Max drawdown" value={fmtPct(c.max_drawdown)} tone="neg" />
        <Card label="VT scale"
          value={c.scale !== null ? fmtNum(c.scale)
            : warm ? `warming up (${c.warmup.n}/${c.warmup.required})` : 'Unavailable'} />
        <Card label="Avg turnover" value={fmtPct(c.avg_turnover)} />
        <Card label="Sum of daily cost fractions" value={fmtPct(c.cum_cost)} tone="neg" />
        <Card label="Mark vs close (gross diagnostic)"
          value={slip ? `${fmtBps(slip.mean_bps)}/day` : "Unavailable"}
          tone={slip ? (slip.mean_bps >= 0 ? "pos" : "neg") : ""} />
      </div>
      {nav && nav.cards.last_scale !== null && <p className="muted">
        latest paper overlay scale: {fmtNum(nav.cards.last_scale)}</p>}
      {warm && <p className="muted">
        vol-target scale needs {c.warmup.required} contiguous base net returns —
        {" "}{c.warmup.required - c.warmup.n} to go</p>}
      {slip
        ? <p className="muted">
            gross mark/close comparison over {slip.n} paired day{slip.n === 1 ? "" : "s"}:
            {" "}{fmtBps(slip.cum_bps)} cumulative · last {slip.last.asof}
            {" "}close {fmtPct(slip.last.close_ret)} vs mark
            {" "}{fmtPct(slip.last.mark_ret)} ({fmtBps(slip.last.bps)})</p>
        : <p className="muted">
            The mark/close comparison is a gross diagnostic, not an observed execution cost.</p>}
    </div>
  );
}

function AccountCardsRow(props: { venue: string; a: PredlabAccount }) {
  const c = props.a.cards;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={c.halted ? "error" : props.a.reconciliation_status === 'reconciled' ? "ok" : "stale"}>{props.venue.toUpperCase()}</Badge>{" "}
      {c.halted && <Badge kind="error">HALTED</Badge>}{" "}
      <span className="muted">
        as of {c.last_asof}{c.dry_run_last ? " (dry-run)" : ""}
        {" "}· {c.n_cycles} cycles</span>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Equity change (unadjusted)" value={fmtPct(c.cum_return)}
          tone={c.cum_return === null ? "" : c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Equity snapshot" value={fmtUsd(c.equity)} />
        <Card label="Cycles" value={fmtNum(c.n_cycles, 0)} />
        <Card label="Orders placed (total)" value={fmtNum(c.orders_total, 0)} />
      </div>
      <p>Reconciliation: {props.a.reconciliation_status ?? 'unavailable'}
        {props.a.reconciliation_reason && <> · {props.a.reconciliation_reason}</>}</p>
      <p className="muted">Equity changes include deposits and withdrawals; they do not measure strategy returns.</p>
    </div>
  );
}

export function PredlabPerformanceTab() {
  const q = useQuery({
    queryKey: ["predlab-performance"], queryFn: api.predlabPerformance,
  });
  const [days, setDays] = useState<number | null>(null);
  const d = correctedPayload(q.data);
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
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  if (!d) return <Section title="Corrected performance unavailable">
    <p>The connected monitor serves legacy measurements. Update the monitor before viewing corrected net performance.</p>
  </Section>;

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
      <Section title="Measurement status">
        <p>{d.measurement!.note}</p>
        <p className="muted">Unknown intervals remain unavailable. No strategy is currently validated.</p>
      </Section>
      {d.books.champion
        ? <CardsRow name="champion" kind="quant" p={d.books.champion}
            nav={navChampion} />
        : <p>Champion: Unavailable · {d.measurement!.books.champion.reason ?? d.measurement!.books.champion.status}</p>}
      {d.books.vt10
        ? <CardsRow name="vt10 (old book)" kind="hybrid" p={d.books.vt10}
            nav={navVt10} />
        : <p>VT10: Unavailable · {d.measurement!.books.vt10.reason ?? d.measurement!.books.vt10.status}</p>}

      {acctTestnet && <AccountCardsRow venue="testnet" a={acctTestnet} />}
      {acctLive && <AccountCardsRow venue="live" a={acctLive} />}

      <Section title="Net paper performance and account equity (indexed to 100)"
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
          anchors={{ quant: null, hybrid: null }}
          labels={{ a: "champion base net", b: "vt10 base net" }}
          extraEquity={extraEquity}
        />
        {(d.books.champion?.rolling_sharpe.length ?? 0) === 0 &&
          <p className="muted">rolling Sharpe requires 30 complete net intervals</p>}
      </Section>

    </>
  );
}
