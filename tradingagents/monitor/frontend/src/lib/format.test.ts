import { describe, expect, it } from "vitest";
import { fmtUsd, fmtPct, fmtNum, fmtBps, fmtWarmup } from "./format";

describe("format", () => {
  it("fmtUsd", () => {
    expect(fmtUsd(10234.567)).toBe("$10,234.57");
    expect(fmtUsd(null)).toBe("—");
  });
  it("fmtPct from fraction", () => {
    expect(fmtPct(-0.0497)).toBe("-4.97%");
    expect(fmtPct(null)).toBe("—");
  });
  it("fmtNum", () => {
    expect(fmtNum(3.178, 2)).toBe("3.18");
    expect(fmtNum(null)).toBe("—");
  });
  it("fmtBps keeps the sign so slippage direction is readable", () => {
    expect(fmtBps(5.04)).toBe("+5.0 bp");
    expect(fmtBps(-2.5)).toBe("-2.5 bp");
    expect(fmtBps(0)).toBe("+0.0 bp");
    expect(fmtBps(null)).toBe("—");
  });
  it("fmtWarmup", () => {
    expect(fmtWarmup(0, 21)).toBe("overlay warming up 0/21");
    expect(fmtWarmup(14, 21)).toBe("overlay warming up 14/21");
  });
});
