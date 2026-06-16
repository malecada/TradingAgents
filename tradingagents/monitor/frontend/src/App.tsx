import { Fragment, useEffect, useState } from "react";
import { PerformanceTab } from "./tabs/PerformanceTab";
import { PositionsTab } from "./tabs/PositionsTab";
import { ExecutionsTab } from "./tabs/ExecutionsTab";
import { DecisionsTab } from "./tabs/DecisionsTab";
import { HealthTab } from "./tabs/HealthTab";
import { RunTab } from "./tabs/RunTab";

const TABS = [
  {
    id: "performance", label: "Performance", el: <PerformanceTab />,
    desc: "Live equity, Sharpe, drawdown and rolling Sharpe for the quant and hybrid books — indexed to 100 and compared against their backtest anchors.",
  },
  {
    id: "positions", label: "Positions", el: <PositionsTab />,
    desc: "Open positions per strategy, queried live from Binance: size, entry, mark, leverage, unrealized PnL and allocation.",
  },
  {
    id: "executions", label: "Executions", el: <ExecutionsTab />,
    desc: "Filled trades and per-strategy analytics — realized PnL, fees, funding and slippage.",
  },
  {
    id: "decisions", label: "Decisions", el: <DecisionsTab />,
    desc: "Per-cycle decision detail: predictions, sizing, risk checks, shadow decisions, and the LLM modulator (hybrid only).",
  },
  {
    id: "health", label: "Health", el: <HealthTab />,
    desc: "Operational health per strategy — cycle timeline, pipeline steps, recent errors and model retrains.",
  },
  {
    id: "run", label: "Run", el: <RunTab />,
    desc: "On-demand prediction: pick a coin, date and quant or hybrid, then study the final call plus every analyst, debate and intermediate output. Display-only — nothing is traded.",
  },
] as const;

export default function App() {
  const initial = window.location.hash.replace("#", "") || "performance";
  const [tab, setTab] = useState(initial);
  useEffect(() => {
    const onHash = () => setTab(window.location.hash.replace("#", "") || "performance");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const active = TABS.find((t) => t.id === tab) ?? TABS[0];
  return (
    <>
      <div className="topbar">
        <h1>Live Monitor</h1>
        <nav className="tabs">
          {TABS.map((t) => (
            <Fragment key={t.id}>
              {/* set the on-demand action tab apart from the read-only views */}
              {t.id === "run" && <span className="tab-sep" aria-hidden="true" />}
              <button
                className={`tab ${t.id === active.id ? "active" : ""} ${t.id === "run" ? "tab-run" : ""}`}
                title={t.desc}
                onClick={() => { window.location.hash = t.id; }}>
                {t.id === "run" ? "▸ Run Prediction" : t.label}
              </button>
            </Fragment>
          ))}
        </nav>
      </div>
      <div className="container">
        <p className="tab-desc">{active.desc}</p>
        {active.el}
      </div>
    </>
  );
}
