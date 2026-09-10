import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Section } from "../components/Section";

export function PredlabGateTab() {
  const q = useQuery({ queryKey: ["predlab-gate"], queryFn: api.predlabGate });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  return (
    <Section title="Suspended after accounting audit">
      <p>{q.data.status === 'suspended_after_audit' && q.data.reason
        ? q.data.reason : 'The historical performance reference and its forward gate were withdrawn after the accounting audit.'}</p>
      <p>No strategy is currently validated. A fresh registration and complete corrected measurements are required before any future evaluation.</p>
      <p className="muted">The original registration remains a historical record. Its threshold, countdown and legacy paper returns cannot establish a pass.</p>
    </Section>
  );
}
