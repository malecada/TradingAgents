"""Render the complete registered evidence in fixed input order; no replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / 'docs/risk-policy-2026-09-10'
OUT = ROOT / 'data/risk-policy/2026-09-10/results'
ARMS = ('A00', 'A10', 'A01', 'A11')
NAMES = dict(A00='Original control', A10='Daily sizing', A01='Wait for new target episode', A11='Both changes')


def number(value, digits=3, percent=False):
    if value is None:
        return 'unavailable'
    return f'{value * (100 if percent else 1):.{digits}f}' + ('%' if percent else '')


def table(headers, rows):
    def escaped(value):
        return str(value).replace('|', '&#124;').replace('\r', '').replace('\n', '<br>')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
        ['| ' + ' | '.join(escaped(v) for v in row) + ' |' for row in rows])


def write(name, text):
    with (DOC / name).open('x') as handle:
        handle.write(text.rstrip() + '\n')


def main():
    result = json.loads((OUT / 'result.json').read_text())
    gate = json.loads((ROOT / 'data/predlab/gates.json').read_text())['risk_policy_2026_09_10']
    review = json.loads((DOC / 'verification/result-review.json').read_text())
    assert review['status'] == 'pass'
    assert review['result_sha256'] == hashlib.sha256((OUT / 'result.json').read_bytes()).hexdigest()
    for name in ('RESULTS.md', 'COST_SENSITIVITY.md', 'SLEEVE_DIAGNOSTICS.md', 'PERIODS.md', 'CONVENTION_SHADOWS.md'):
        assert not (DOC / name).exists(), 'report already exists: ' + name
    assert [c['id'] for c in result['cells']] == [c['id'] for c in gate['cells']]
    cells = result['cells']
    by_id = {c['id']: c for c in cells}
    summaries, primary_rows, cost_rows, sleeve_rows, period_rows, log_rows, contrast_rows = [], [], [], [], [], [], []
    conventions = dict(total_return_sign_changes=0, sharpe_sign_changes=0,
                       direct_sharpe_order_changes=0, direct_total_return_order_changes=0,
                       complete_shadows=0, complete_direct_shadow_comparisons=0,
                       sharpe_eligible=0, total_return_eligible=0,
                       direct_sharpe_eligible=0, direct_total_return_eligible=0)
    def index_metrics(cell, variant='primary'):
        return cell['metrics']['variants'][variant]['index'].get('metrics', {})
    for arm in ARMS:
        selected = [c for c in cells if c['arm'] == arm]
        valid = [c for c in selected if c['metrics']['variants']['primary']['index']['status'] == 'complete']
        sleeve_records = [s for c in selected for s in c['metrics']['variants']['primary']['sleeves'].values() if s['status'] == 'complete']
        ds = [s['diagnostics'] for s in sleeve_records]
        paired = [c for c in valid if index_metrics(by_id[c['configuration']['name']+'|A00'])]
        finite_sr = [c for c in valid if index_metrics(c).get('sharpe') is not None]
        mean_up = sum(index_metrics(c)['mean_return'] > index_metrics(by_id[c['configuration']['name']+'|A00'])['mean_return']
                      for c in valid if index_metrics(by_id[c['configuration']['name']+'|A00']))
        dd_up = sum(index_metrics(c)['max_drawdown'] > index_metrics(by_id[c['configuration']['name']+'|A00'])['max_drawdown']
                    for c in valid if index_metrics(by_id[c['configuration']['name']+'|A00']))
        def total(field):
            return sum(d[field] for d in ds) if ds else 'unavailable'
        summaries.append([arm, len(valid), len(ds), f"{sum(index_metrics(c)['total_return'] > 0 for c in valid)}/{len(valid)}",
            f"{sum(index_metrics(c)['sharpe'] > 0 for c in finite_sr)}/{len(finite_sr)}",
            '—' if arm == 'A00' else f'{mean_up}/{len(paired)}', '—' if arm == 'A00' else f'{dd_up}/{len(paired)}',
            total('active_rows'), total('waiting_rows'), total('price_stops'),
            sum(d['first_halt'] is not None for d in ds) if ds else 'unavailable',
            sum(d['risk_counts']['applied']['above_nominal_budget'] for d in ds) if ds else 'unavailable'])
    for cell in cells:
        config, arm = cell['configuration']['name'], cell['arm']
        primary = cell['metrics']['variants']['primary']
        m = primary['index'].get('metrics', {})
        ds = {coin: s.get('diagnostics', {}) for coin, s in primary['sleeves'].items()}
        primary_rows.append([config, arm, primary['index']['status'], number(m.get('sharpe')),
            number(m.get('annual_mean'), 2, True), number(m.get('total_return'), 2, True),
            number(m.get('max_drawdown'), 2, True),
            '/'.join(str(ds[c].get('active_rows', 'unavailable')) for c in gate['coins']),
            '/'.join(str(ds[c].get('waiting_rows', 'unavailable')) for c in gate['coins']),
            primary['index'].get('reason') or m.get('sharpe_reason') or '—'])
        for variant in gate['variants']:
            v = cell['metrics']['variants'][variant]
            vm = v['index'].get('metrics', {})
            cost_rows.append([config, arm, variant, v['index']['status'], number(vm.get('sharpe')),
                number(vm.get('annual_mean'), 2, True), number(vm.get('total_return'), 2, True),
                number(vm.get('max_drawdown'), 2, True), v['index'].get('reason') or vm.get('sharpe_reason') or '—'])
        for coin in gate['coins']:
            s, d = primary['sleeves'][coin], ds[coin]
            sm = s.get('metrics', {})
            halt = d.get('first_halt')
            sleeve_rows.append([config, arm, coin, s['status'], number(sm.get('sharpe')),
                number(sm.get('total_return'), 2, True), number(sm.get('max_drawdown'), 2, True),
                d.get('active_rows', 'unavailable'), d.get('waiting_rows', 'unavailable'),
                d.get('halted_cash_rows', 'unavailable'), halt['date'][:10] if halt else 'none' if s['status'] == 'complete' else 'unavailable',
                number(d.get('exposures', {}).get('applied', {}).get('integrated_absolute'), 2),
                number(d.get('risk_distributions', {}).get('applied', {}).get('p90'), 2, True),
                d.get('price_stops', 'unavailable'), s.get('reason') or sm.get('sharpe_reason') or '—'])
        saved_periods = {(p['start'], p['end']): p for p in primary['index'].get('periods', [])}
        if primary['index']['status'] == 'complete':
            assert list(saved_periods) == [tuple(p) for p in gate['reporting']['periods']]
        for start, end in gate['reporting']['periods']:
            period = saved_periods.get((start, end))
            pm = period['metrics'] if period else {}
            status = pm.get('status', 'unavailable')
            period_rows.append([config, arm, start, end, status, pm.get('n_bars', 'unavailable'),
                number(pm.get('sharpe')), number(pm.get('total_return'), 2, True), number(pm.get('max_drawdown'), 2, True),
                primary['index'].get('reason') or pm.get('sharpe_reason') or '—'])
        shadow = cell['metrics']['log_shadow']
        lm = shadow['index'].get('metrics', {})
        log_rows.append([config, arm, shadow['index']['status'], number(m.get('sharpe')), number(lm.get('sharpe')),
            number(m.get('total_return'), 2, True), number(lm.get('total_return'), 2, True)])
        if shadow['index']['status'] == 'complete' and m:
            conventions['complete_shadows'] += 1
            for field in ('sharpe', 'total_return'):
                if m[field] is not None and lm[field] is not None:
                    conventions[field + '_eligible'] += 1
                    if (m[field] > 0) != (lm[field] > 0):
                        conventions[field + '_sign_changes'] += 1
        if arm != 'A00':
            control = by_id[config + '|A00']
            cm = index_metrics(control)
            clm = control['metrics']['log_shadow']['index'].get('metrics', {})
            delta = {k: m[k] - cm[k] if m.get(k) is not None and cm.get(k) is not None else None
                     for k in ('sharpe', 'annual_mean', 'total_return', 'max_drawdown')}
            contrast_rows.append([config, arm, number(delta['sharpe']), number(delta['annual_mean'], 2, True),
                number(delta['total_return'], 2, True), number(delta['max_drawdown'], 2, True)])
            if m and cm and lm and clm:
                conventions['complete_direct_shadow_comparisons'] += 1
                for field in ('sharpe', 'total_return'):
                    if all(x.get(field) is not None for x in (m, cm, lm, clm)):
                        conventions['direct_' + field + '_eligible'] += 1
                        simple_delta, log_delta = m[field] - cm[field], lm[field] - clm[field]
                        if (simple_delta > 0) != (log_delta > 0):
                            conventions['direct_' + field + '_order_changes'] += 1
    write('RESULTS.md', '\n\n'.join([
        '# Factor sizing and stop re-entry comparison — September 10, 2026',
        '**Zero strategies are validated by this retrospective comparison.** All eighteen original factor configurations were retained in a fixed four-arm design. The comparison measures behavior on spent development history; it has no adoption gate or winner selection.',
        'A00 preserves original behavior; A10 refreshes volatility sizing daily; A01 waits for the saved raw target to go flat or opposite after a price stop; A11 combines the changes. The permanent15% drawdown halt remains absorbing. A long-only target may never release the waiting policy, producing long cash periods.',
        '## Fixed-arm overview',
        'Counts refer to18 correlated configuration indices or36 separately simulated sleeves per arm. Active/waiting dates are sums over those sleeve books, not an executable portfolio. “Improved” is a descriptive point difference versus the same configuration’s control. A positive DD difference means a smaller drawdown. Flatness and lower exposure can reduce losses without establishing an edge.',
        table(['Arm','Complete indices /18','Measured sleeves /36','Positive return /measured','Positive SR /finite','Higher mean /paired','Smaller DD /paired','Active sleeve-days','Waiting sleeve-days','Price stops','Halted measured sleeves','Active dates risk >15%'], summaries),
        '## All72 primary identities',
        'Sharpe uses sqrt365, ddof1 and zero hurdle; mean is arithmetic annualized. Returns and drawdowns include all1,240 daily observations and initial NAV. BTC/ETH counts retain both sleeves. Undefined ratios remain unavailable; no cash dates are removed.',
        table(['Configuration','Arm','Status','SR','Annual mean','Compound return','Max DD','Active BTC/ETH','Waiting BTC/ETH','Unavailable/undefined reason'], primary_rows),
        '## All54 changes versus their original controls',
        'Percentage-valued differences below are percentage points. These are paired full-calendar descriptive differences; there are no p-values, bootstrap selection or independent replication claims. The complete factorial contrasts and sleeve-level cost/exposure/risk differences are retained in result.json.',
        table(['Configuration','Arm','ΔSR','Δannual mean','Δcompound return','Δmax DD'], contrast_rows),
        '## Accounting convention forensics',
        f"Of72 registered shadows, {conventions['complete_shadows']} are complete. Positive/nonpositive Sharpe labels change in {conventions['sharpe_sign_changes']}/{conventions['sharpe_eligible']} finite comparisons; compound-return labels change in {conventions['total_return_sign_changes']}/{conventions['total_return_eligible']}. Among54 registered direct contrasts, positive/nonpositive ΔSharpe ordering changes in {conventions['direct_sharpe_order_changes']}/{conventions['direct_sharpe_eligible']} finite comparisons and Δcompound-return ordering in {conventions['direct_total_return_order_changes']}/{conventions['direct_total_return_eligible']}. Undefined ratios are excluded only from the corresponding finite diagnostic denominator, while their identities remain in the tables. Invalid-log arithmetic is never used to choose a policy. Exposure, stops, funding and fees remain frozen in these shadows.",
        '## Complete evidence and limits',
        '[Cost sensitivities](COST_SENSITIVITY.md) retain all288 index evaluation identities. [Primary sleeve diagnostics](SLEEVE_DIAGNOSTICS.md) retain all144 primary sleeve identities. [Fixed periods](PERIODS.md) retain216 periods and [invalid convention shadows](CONVENTION_SHADOWS.md) retain72 identities. Result JSON preserves all576 registered sleeve books with explicit unavailable reasons where applicable; available trace/daily/stop artifacts retain detailed component attribution.',
        f"Independent verification passed {review['counts']['assertions']:,} assertions across {review['counts']['traces']}/576 traces, {review['counts']['control_traces']}/144 original control traces and {review['counts']['control_return_frames']}/72 original control return frames. The checker reconstructs every charged leg and target/stop transition from saved evidence without replaying policies. Source: `{result['git_commit']}`. Result SHA-256: `{hashlib.sha256((OUT/'result.json').read_bytes()).hexdigest()}`.",
        'The daily price proxies, assumed signed3bp/day funding, threshold stop fills and separate-sleeve index remain limitations. Cost variants each have their own stops and halt dates. Reduced risk exposure is not proof of executable alpha. The old holdout remains spent; [the prospective validation plan](fresh-validation-plan.md) requires a separately frozen candidate/family, venue economics, power/gates and a future observation window. No provider contact, paid-data purchase, paper restart or VPS deployment occurred.'
    ]))
    write('COST_SENSITIVITY.md', '# All288 fixed cost evaluations\n\nEach case is independently simulated; Sharpe and DD use the full calendar. These are qualified development measurements.\n\n' +
        table(['Configuration','Arm','Costs','Status','SR','Annual mean','Compound return','Max DD','Unavailable/undefined reason'], cost_rows))
    write('SLEEVE_DIAGNOSTICS.md', '# All144 primary sleeve books\n\nExposure is integrated absolute target weight in weight-days. Risk P90 is the nominal |weight|×sigma252 proxy on active dates, not realized account volatility. Dollar components remain separate in result.json.\n\n' +
        table(['Configuration','Arm','Coin','Status','SR','Return','Max DD','Active','Waiting','Post-halt cash','First halt','Exposure','Risk P90','Stops','Unavailable/undefined reason'], sleeve_rows))
    write('PERIODS.md', '# Fixed period comparisons\n\nCash and halt days remain on each complete period clock; an all-cash period is not independent evidence of success.\n\n' +
        table(['Configuration','Arm','Start','End','Status','Days','SR','Return','Max DD','Unavailable/undefined reason'], period_rows))
    write('CONVENTION_SHADOWS.md', '# All72 invalid convention shadows\n\nFrozen exposures and stop/cost schedules only. Log-return PnL is invalid accounting and cannot qualify a policy.\n\n' +
        table(['Configuration','Arm','Shadow status','Simple SR','Invalid log SR','Simple return','Invalid log return'], log_rows))
    print(json.dumps({'reports': 5, 'primary_rows': len(primary_rows), 'contrasts': len(contrast_rows),
        'cost_rows': len(cost_rows), 'sleeve_rows': len(sleeve_rows), 'period_rows': len(period_rows),
        'convention_counts': conventions}, indent=2))


if __name__ == '__main__':
    main()
