import { describe, it, expect } from 'vitest';
import * as guard from './predlabGuard';
import type { PredlabPerformanceResp } from '../types';

describe('corrected measurement admission', () => {
  it('rejects an incomplete compatibility contract', () => {
    for (const d of [
      { books: { champion: null, vt10: null }, measurement: { status: 'missing', books: {} } },
      { measurement: { status: 'missing', books: { champion: {}, vt10: {} } } },
    ]) expect(guard.correctedPayload(d as unknown as PredlabPerformanceResp)).toBeNull();
  });
  it('withholds old API gross returns from corrected performance', () => {
    const old = { books: { champion: { cards: { cum_return: 3. } }, vt10: null },
      reference: { ovl_sr_full: 1.892 } } as unknown as PredlabPerformanceResp;
    expect(guard.correctedPayload(old)).toBeNull();
  });
  it('retains an explicitly incomplete corrected payload for honest unavailable display', () => {
    const next = { books: { champion: null, vt10: null },
      measurement: { status: 'incomplete', note: 'Funding missing', books: {
        champion: { status: 'incomplete', reason: 'Funding missing', journal: 'journal_champion_v2.jsonl' },
        vt10: { status: 'missing', reason: null, journal: null } } } } as unknown as PredlabPerformanceResp;
    expect(guard.correctedPayload(next)).toBe(next);
  });
});
