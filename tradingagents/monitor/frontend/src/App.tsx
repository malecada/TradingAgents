import { Fragment, useEffect, useState } from "react";
import { PredlabPerformanceTab } from "./tabs/PredlabPerformanceTab";
import { PredlabBookTab } from "./tabs/PredlabBookTab";
import { PredlabGateTab } from "./tabs/PredlabGateTab";
import { PredlabOpsTab } from "./tabs/PredlabOpsTab";
import { LegacyTab } from "./tabs/LegacyTab";

const TABS = [
  {
    id: "performance", label: "Performance", el: <PredlabPerformanceTab />,
    desc: "Corrected net paper measurements for champion and VT10, with explicit gaps, warmup and account reconciliation status.",
  },
  {
    id: "book", label: "Book", el: <PredlabBookTab />,
    desc: "Saved target weights, universe membership and volatility scale. Composition is an operational diagnostic; it does not establish complete net measurement.",
  },
  {
    id: "gate", label: "Gate", el: <PredlabGateTab />,
    desc: "The historical validation gate is suspended after the accounting audit.",
  },
  {
    id: "ops", label: "Ops", el: <PredlabOpsTab />,
    desc: "Journal versions, freshness, measurement completeness and missing dates for both paper books.",
  },
  {
    id: "legacy", label: "Legacy", el: <LegacyTab />,
    desc: "Historical quant/hybrid diagnostics. Their superseded performance references do not validate a strategy.",
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
        <p className="muted">Research status: no validated strategies. Historical reference results remain withdrawn.</p>
        {active.el}
      </div>
    </>
  );
}
