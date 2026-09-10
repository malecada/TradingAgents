import { describe, expect, it } from "vitest";
import { safeAccount, safeNav } from "./predlabGuard";

const NAV = { series: [], cards: {
  nav_cum_return: 0.05, active_days: 3,
  warmup: { n: 21, required: 21 }, last_scale: 0.4,
} };
const ACCOUNT = { series: [], cards: {
  cum_return: 0.02, equity: 1000, n_cycles: 5, orders_total: 3,
  last_asof: "2026-08-20", dry_run_last: false, halted: false,
} };

describe("predlabGuard", () => {
  // The scenario the crash report was about: a backend deployed without
  // this feature (or serving a degraded payload) omits the top-level
  // nav/account keys ENTIRELY, not just null-valued per-book/venue.
  it("payload missing nav/account keys entirely -> null, never throws", () => {
    const d = { books: {} } as never;
    expect(() => safeNav(d, "champion")).not.toThrow();
    expect(() => safeAccount(d, "testnet")).not.toThrow();
    expect(safeNav(d, "champion")).toBeNull();
    expect(safeAccount(d, "testnet")).toBeNull();
  });

  it("undefined payload -> null, never throws", () => {
    expect(safeNav(undefined, "champion")).toBeNull();
    expect(safeAccount(undefined, "live")).toBeNull();
  });

  it("null payload -> null, never throws", () => {
    expect(safeNav(null, "vt10")).toBeNull();
    expect(safeAccount(null, "live")).toBeNull();
  });

  it("nav/account present but per-book/venue entry is null -> null", () => {
    const d = { nav: { champion: null, vt10: null },
                account: { testnet: null, live: null } };
    expect(safeNav(d, "champion")).toBeNull();
    expect(safeAccount(d, "live")).toBeNull();
  });

  it("populated entry is returned as-is", () => {
    const d = { nav: { champion: NAV, vt10: null },
                account: { testnet: ACCOUNT, live: null } };
    expect(safeNav(d, "champion")).toBe(NAV);
    expect(safeAccount(d, "testnet")).toBe(ACCOUNT);
  });
});
