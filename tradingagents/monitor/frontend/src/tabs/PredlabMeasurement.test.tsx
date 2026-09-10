import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PredlabPerformanceTab } from './PredlabPerformanceTab';
import { PredlabGateTab } from './PredlabGateTab';
import { PredlabOpsTab } from './PredlabOpsTab';
import type { ReactNode } from 'react';

function render(key: string, data: unknown, child: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity, retry: false } } });
  client.setQueryData([key], data);
  const html = renderToStaticMarkup(<QueryClientProvider client={client}>{child}</QueryClientProvider>);
  client.clear();
  return html;
}

describe('predlab audit status in rendered tabs', () => {
  it('withholds legacy gross measurements from the performance view', () => {
    const html = render('predlab-performance', {
      books: { champion: null, vt10: null }, reference: { ovl_sr_full: 1.892, ovl_maxdd: -0.1 },
    }, <PredlabPerformanceTab />);
    expect(html).toContain('Corrected performance unavailable');
    expect(html).not.toContain('1.89');
    expect(html).not.toContain('Frozen dev reference');
  });

  it('shows an incomplete funding measurement instead of a return or warmup claim', () => {
    const html = render('predlab-performance', {
      books: { champion: null, vt10: null }, measurement: {
        status: 'incomplete', note: 'Funding missing', books: {
          champion: { status: 'incomplete', reason: 'Funding missing', journal: 'journal_champion_v2.jsonl' },
          vt10: { status: 'missing', reason: 'No journal', journal: null },
        },
      },
    }, <PredlabPerformanceTab />);
    expect(html).toContain('Funding missing');
    expect(html).toContain('Unavailable');
    expect(html).not.toContain('0.00%');
  });

  it('suspends the withdrawn gate even when connected to the older API', () => {
    const html = render('predlab-gate', {
      window_start: '2026-08-05', earliest_eval: '2027-01-02', days_elapsed: 30,
      days_remaining: 120, threshold_sr: 0.946, criteria: [],
      running: { sr: 2, n_returns: 30, note: '' }, informational: true,
    }, <PredlabGateTab />);
    expect(html).toContain('Suspended after accounting audit');
    expect(html).not.toContain('0.946');
    expect(html).not.toContain('Days remaining');
  });

  it('does not describe a broken non-null measurement as VT warmup', () => {
    const html = render('predlab-performance', {
      books: { champion: { equity: [], drawdown: [], rolling_sharpe: [], slippage: null,
        measurement_status: 'incomplete', measurement_reason: 'Funding missing',
        cards: { cum_return: null, sharpe: null, max_drawdown: null, scale: null,
          warmup: { n: 20, required: 20 }, avg_turnover: null, cum_cost: null,
          last_asof: '2026-09-09', n_days: 21 } }, vt10: null },
      measurement: { status: 'incomplete', note: 'Funding missing', books: {
        champion: { status: 'incomplete', reason: 'Funding missing', journal: 'journal_champion_v2.jsonl' },
        vt10: { status: 'missing', reason: null, journal: null } } },
      account: { testnet: { series: [], reconciliation_status: 'reconciled', cards: {
        cum_return: null, equity: 100, n_cycles: 1, orders_total: 0,
        last_asof: '2026-09-09', dry_run_last: false, halted: false } }, live: null },
    }, <PredlabPerformanceTab />);
    expect(html).not.toContain('warming up');
    expect(html).toContain('Unavailable');
    expect(html).toContain('badge ok');
    expect(html).not.toContain('21 intervals');
  });

  it('distinguishes a fresh legacy file from a corrected measurement', () => {
    const html = render('predlab-health', {
      books: { champion: { last_asof: '2026-09-09', written_utc: '2026-09-10', stale: false,
        rows: 38, malformed: 0, gaps: [], journal_version: 1, measurement_status: 'legacy_only',
        measurement_reason: 'Legacy gross diagnostic; net performance unavailable', legacy_rows: 38 }, vt10: null },
      heartbeat_note: '',
    }, <PredlabOpsTab />);
    expect(html).toContain('FRESH');
    expect(html).toContain('net performance unavailable');
    expect(html).not.toContain('>OK<');
  });
});
