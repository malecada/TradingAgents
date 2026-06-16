import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("adhoc api", () => {
  it("adhocRun posts body as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ run_id: "abc" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const r = await api.adhocRun({ coin: "bitcoin", date: "2026-05-01", strategy: "quant" });
    expect(r.run_id).toBe("abc");
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/adhoc/run");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body)).toMatchObject({ coin: "bitcoin", strategy: "quant" });
  });

  it("adhocStatus GETs the run id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ status: "done", outputs: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const r = await api.adhocStatus("abc");
    expect(r.status).toBe("done");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/adhoc/status/abc");
  });
});
