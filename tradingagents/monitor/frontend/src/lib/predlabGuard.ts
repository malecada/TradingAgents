import type {
  PredlabAccount, PredlabBookName, PredlabNav, PredlabPerformanceResp,
  PredlabVenue,
} from "../types";

/** Payload shape this guard tolerates: a backend deployed without the
 *  NAV/account feature (or serving an older/degraded payload) may omit
 *  the `nav` / `account` top-level keys entirely — not just null them
 *  out per-book/venue. Every accessor here must survive that. */
type MaybePerf = Pick<PredlabPerformanceResp, "nav" | "account"> | null | undefined;

/** `d?.nav.champion` throws when `d.nav` itself is undefined — this is
 *  the safe form: missing top-level key, missing per-book entry, and an
 *  explicit null all resolve to null, never throw. */
export function safeNav(d: MaybePerf, book: PredlabBookName): PredlabNav | null {
  return d?.nav?.[book] ?? null;
}

/** Same contract as {@link safeNav} for the per-venue account block. */
export function safeAccount(d: MaybePerf, venue: PredlabVenue): PredlabAccount | null {
  return d?.account?.[venue] ?? null;
}
