import { describe, expect, it } from "vitest";
import { rebaseTo100, sliceFromDays } from "./rebase";

const pts = [
  { ts: "2026-06-01T00:00:00+00:00", value: 200 },
  { ts: "2026-06-02T00:00:00+00:00", value: 220 },
  { ts: "2026-06-03T00:00:00+00:00", value: 210 },
];

describe("rebaseTo100", () => {
  it("rebases first point to 100", () => {
    const out = rebaseTo100(pts);
    expect(out[0].value).toBe(100);
    expect(out[1].value).toBeCloseTo(110);
    expect(out[2].value).toBeCloseTo(105);
  });
  it("empty input -> empty output", () => {
    expect(rebaseTo100([])).toEqual([]);
  });
});

describe("sliceFromDays", () => {
  it("keeps only points within N days of the last point", () => {
    expect(sliceFromDays(pts, 1).length).toBe(2);
    expect(sliceFromDays(pts, 9999)).toEqual(pts);
  });
  it("null days -> all", () => {
    expect(sliceFromDays(pts, null)).toEqual(pts);
  });
  it("drops points with unparseable timestamps", () => {
    const withBad = [{ ts: "start", value: 100 }, ...pts];
    expect(sliceFromDays(withBad, 9999)).toEqual(pts);
  });
});
import type { Point as NullablePoint } from '../types';

it('retains unknown dates without converting an unavailable measurement to zero', () => {
  const points = [{ ts: '2026-09-01', value: 100 }, { ts: '2026-09-02', value: null },
    { ts: '2026-09-03', value: null }] as NullablePoint[];
  expect(rebaseTo100(points)).toEqual(points);
});

it('does not restart a sliced unknown NAV at a later observed value', () => {
  const points = [{ ts: '2026-09-02', value: null }, { ts: '2026-09-03', value: 110 }] as NullablePoint[];
  expect(rebaseTo100(points)).toEqual(points.map(p => ({ ...p, value: null })));
});
