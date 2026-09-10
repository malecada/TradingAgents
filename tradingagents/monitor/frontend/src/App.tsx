import { Fragment, useEffect, useState } from "react";
import { PredlabPerformanceTab } from "./tabs/PredlabPerformanceTab";
import { PredlabBookTab } from "./tabs/PredlabBookTab";
import { PredlabGateTab } from "./tabs/PredlabGateTab";
import { PredlabOpsTab } from "./tabs/PredlabOpsTab";
import { LegacyTab } from "./tabs/LegacyTab";

const TABS = [
  {
    id: "performance", label: "Performance", el: <PredlabPerformanceTab />,
    desc: "Predlab champion (ewma_20 low-vol LS + vt15_b100) and old vt10 paper books — equity compounded from realized returns, Sharpe, drawdown, cost drag, plus the frozen dev backtest reference.",
  },
  {
    id: "book", label: "Book", el: <PredlabBookTab />,
    desc: "Today's cross-sectional book: 40 longs / 40 shorts at ±2.5%, universe membership, breadth and vol-target scale.",
  },
  {
    id: "gate", label: "Gate", el: <PredlabGateTab />,
    desc: "Sealed one-shot forward tracker — informational only; the evaluation happens once, earliest 2027-01-02.",
  },
  {
    id: "ops", label: "Ops", el: <PredlabOpsTab />,
    desc: "Journal freshness, gaps and malformed-line counts for both paper books, plus the backup-branch heartbeat.",
  },
  {
    id: "legacy", label: "Legacy", el: <LegacyTab />,
    desc: "Read-only archive of the decommissioned V5 8-coin quant/hybrid books (journals frozen 2026-08-06).",
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
              {/* set the read-only archive tab apart from the live predlab views */}
              {t.id === "legacy" && <span className="tab-sep" aria-hidden="true" />}
              <button
                className={`tab ${t.id === active.id ? "active" : ""} ${t.id === "legacy" ? "tab-run" : ""}`}
                title={t.desc}
                onClick={() => { window.location.hash = t.id; }}>
                {t.id === "legacy" ? "▸ Legacy" : t.label}
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
