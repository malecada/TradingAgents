import { useState } from "react";
import { PerformanceTab } from "./PerformanceTab";
import { PositionsTab } from "./PositionsTab";
import { ExecutionsTab } from "./ExecutionsTab";
import { DecisionsTab } from "./DecisionsTab";
import { HealthTab } from "./HealthTab";

const SUBTABS = [
  { id: "performance", label: "Performance", el: <PerformanceTab /> },
  { id: "positions", label: "Positions", el: <PositionsTab /> },
  { id: "executions", label: "Executions", el: <ExecutionsTab /> },
  { id: "decisions", label: "Decisions", el: <DecisionsTab /> },
  { id: "health", label: "Health", el: <HealthTab /> },
] as const;

/** Read-only archive of the decommissioned V5 quant/hybrid books. */
export function LegacyTab() {
  const [sub, setSub] = useState<string>("performance");
  const active = SUBTABS.find((t) => t.id === sub) ?? SUBTABS[0];
  return (
    <>
      <p className="badge stale" style={{ marginTop: 10 }}>
        V5 books decommissioned 2026-08-06 — read-only archive. Journals
        frozen; live-exchange panels may show STALE.
      </p>
      <div className="pills" style={{ marginTop: 8 }}>
        {SUBTABS.map((t) => (
          <button key={t.id} className={`pill ${t.id === active.id ? "active" : ""}`}
            onClick={() => setSub(t.id)}>{t.label}</button>
        ))}
      </div>
      {active.el}
    </>
  );
}
