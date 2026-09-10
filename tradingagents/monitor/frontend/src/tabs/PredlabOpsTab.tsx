import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import type { PredlabBookHealth, PredlabBookName } from "../types";

function BookHealth(props: { name: PredlabBookName; h: PredlabBookHealth | null }) {
  const h = props.h;
  return (
    <Section title={`${props.name} journal`}>
      {!h ? <p className="muted">no journal</p> : (
        <>
          <p>
            <Badge kind={h.stale ? "stale" : "ok"}>
              {h.stale ? "STALE" : "OK"}</Badge>{" "}
            last row {h.last_asof} · written {h.written_utc ?? "—"} ·
            {" "}{h.rows} rows
            {h.malformed > 0 && <> · <Badge kind="error">
              {h.malformed} malformed lines</Badge></>}
          </p>
          {h.gaps.length > 0 && (
            <table>
              <thead><tr><th>Missing date</th><th>Status</th></tr></thead>
              <tbody>
                {h.gaps.map((g) => (
                  <tr key={g.date}><td>{g.date}</td>
                    <td>{g.known
                      ? <span className="muted">known (scheduler off)</span>
                      : <Badge kind="error">unexplained</Badge>}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </Section>
  );
}

export function PredlabOpsTab() {
  const q = useQuery({ queryKey: ["predlab-health"], queryFn: api.predlabHealth });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  return (
    <>
      <BookHealth name="champion" h={q.data.books.champion} />
      <BookHealth name="vt10" h={q.data.books.vt10} />
      <p className="muted">{q.data.heartbeat_note}</p>
    </>
  );
}
