import type {
  PredlabAccount, PredlabBookName, PredlabNav, PredlabPerformanceResp,
  PredlabVenue,
} from "../types";

/** Payload shape this guard tolerates: a backend deployed without the
 *  NAV/account feature (or serving an older/degraded payload) may omit
 *  the `nav` / `account` top-level keys entirely — not just null them
 *  out per-book/venue. Every accessor here must survive that. */
type MaybePerf = Pick<PredlabPerformanceResp, "nav" | "account"> | null | undefined;

/** Older APIs expose gross diagnostics under the performance keys. Require
 * the explicit audit-status contract before rendering corrected measurements. */
export function correctedPayload(d: PredlabPerformanceResp | null | undefined): PredlabPerformanceResp | null {
  if (!d?.measurement?.status || !d.books || !d.measurement.books) return null;
  for (const book of ['champion', 'vt10'] as const) {
    const descriptor = d.measurement.books[book];
    if (!(book in d.books) || !descriptor || typeof descriptor.status !== 'string'
        || !(descriptor.reason === null || typeof descriptor.reason === 'string')) return null;
  }
  return d;
}

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
