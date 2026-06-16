import { describe, expect, it } from "vitest";
import { isTerminal, pollInterval } from "./adhoc";

describe("adhoc status helpers", () => {
  it("isTerminal", () => {
    expect(isTerminal("done")).toBe(true);
    expect(isTerminal("error")).toBe(true);
    expect(isTerminal("running")).toBe(false);
    expect(isTerminal("queued")).toBe(false);
  });
  it("pollInterval stops on terminal", () => {
    expect(pollInterval("running")).toBe(2000);
    expect(pollInterval("done")).toBe(false);
    expect(pollInterval(undefined)).toBe(2000);
  });
});
