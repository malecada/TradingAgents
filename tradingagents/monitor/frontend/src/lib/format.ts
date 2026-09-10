export function fmtUsd(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 2,
  });
}

/** v is a FRACTION (-0.05 => "-5.00%"). */
export function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(2)}%`;
}

/** v is already in BASIS POINTS; the sign is kept (mark leg minus close leg). */
export function fmtBps(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${v < 0 ? "" : "+"}${v.toFixed(1)} bp`;
}

export function fmtNum(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(digits);
}

/** Label for an overlay/NAV series that hasn't accrued enough realized
 *  returns to go live yet (vol-target scale warmup, 21 returns). */
export function fmtWarmup(n: number, required: number): string {
  return `overlay warming up ${n}/${required}`;
}
