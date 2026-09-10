"""Independent checks of saved risk-policy evidence; never invokes a backtest.

Only the new output namespace and registered old references may be read.
Algebra is reconstructed directly from saved books, prices and raw targets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
KEY = 'risk_policy_2026_09_10'
COUNTS = {'assertions': 0, 'traces': 0, 'control_traces': 0, 'return_frames': 0,
          'control_return_frames': 0, 'shadows': 0}


def require(condition, label):
    COUNTS['assertions'] += 1
    if not bool(condition):
        raise AssertionError(label)


def near(actual, expected, label, atol=1e-9):
    actual, expected = np.asarray(actual, float), np.asarray(expected, float)
    require(actual.shape == expected.shape, label + ': shape')
    require(np.allclose(actual, expected, atol=atol, rtol=1e-10, equal_nan=True), label)


def dates(values):
    return pd.DatetimeIndex(pd.to_datetime(values, utc=True)).tz_localize(None)


def sigma_reference(close):
    close = np.asarray(close, float)
    visible = np.r_[close[0], close[:-1]]
    logs = np.r_[np.nan, np.log(visible[1:] / visible[:-1])]
    result = np.full(len(close), np.nan)
    for i in range(20, len(close)):
        result[i] = np.std(logs[i-19:i+1], ddof=1) * np.sqrt(252)
    return result


def check_trace(trace, targets, arm, costs):
    """Check actual saved decisions, marks, every charge and absorbing halts."""
    require(len(trace) == 1240 and len(targets) == 1241, 'full clocks')
    require(dates(trace.date).equals(dates(targets.Date)[1:]), 'target/trace dates')
    target = targets.target.to_numpy(float)
    sigmas = sigma_reference(targets.Close)
    require(np.isfinite(target).all(), 'finite raw targets')
    require(np.isfinite(trace[['exposure', 'nav_before', 'nav_after']]).all().all(), 'finite books')
    raw, volatility = target[1:], sigmas[1:]
    nav, after = trace.nav_before.to_numpy(), trace.nav_after.to_numpy()
    w, r = trace.exposure.to_numpy(), trace.mark_return.to_numpy()
    held = np.r_[0., trace.closing_notional.to_numpy()[:-1]]
    near(nav, np.r_[10000., after[:-1]], 'NAV continuity')
    near(trace.pre_nav, nav, 'pre NAV alias')
    near(trace.post_nav, after, 'post NAV alias')
    turnover = abs(nav * w - held)
    fee = costs['fee_rate'] + costs['slippage'] + costs['spread']
    gross, carry = nav * w * r, -nav * w * costs['funding_rate']
    entry_fee, entry_impact = turnover * fee, costs['price_impact'] * turnover**2 / nav
    pre_exit = nav + gross + carry - entry_fee - entry_impact
    marked = nav * w * (1 + r)
    exits = trace.exit_executed.to_numpy(bool)
    exit_turnover = np.where(exits, abs(marked), 0.)
    exit_fee, exit_impact = exit_turnover * fee, costs['price_impact'] * exit_turnover**2 / pre_exit
    for name, expected in [('gross_dollars', gross), ('funding_dollars', carry),
            ('entry_turnover_dollars', turnover), ('entry_fee_dollars', entry_fee),
            ('entry_impact_dollars', entry_impact), ('exit_turnover_dollars', exit_turnover),
            ('exit_fee_dollars', exit_fee), ('exit_impact_dollars', exit_impact),
            ('exit_notional', np.where(exits, marked, 0.)),
            ('closing_notional', np.where(exits, 0., marked)),
            ('fee_dollars', entry_fee + exit_fee), ('impact_dollars', entry_impact + exit_impact),
            ('turnover_dollars', turnover + exit_turnover),
            ('nav_after', pre_exit - exit_fee - exit_impact)]:
        near(trace[name], expected, name)
    near(trace.net_return, after / nav - 1, 'simple net returns', 1e-12)
    near(trace.target_position, w, 'executed target', 1e-12)
    require((nav > 0).all() and (after > 0).all(), 'positive NAV')
    blocked, halted, last_w, anchor, peak = 0, False, 0., 0., 10000.
    expected_weights, expected_marks, expected_anchors = [], [], []
    for j, row in enumerate(trace.itertuples(index=False)):
        direction = int(np.sign(raw[j]))
        before, release, waiting = blocked, None, False
        if halted:
            expected_w, reason = 0., 'permanent_halt'
        else:
            if blocked and direction != blocked:
                blocked = 0
                release = 'raw_flat' if direction == 0 else 'raw_opposite'
            if direction == 0:
                expected_w, reason = 0., 'raw_flat'
            elif blocked:
                expected_w, reason, waiting = 0., 'waiting_same_direction', True
            elif arm in ('A10', 'A11'):
                require(np.isfinite(volatility[j]) and volatility[j] > 0, 'admitted daily sigma')
                expected_w = direction * min(3., .15 / volatility[j])
                reason = 'daily_resize'
            else:
                expected_w, reason = raw[j], 'saved_target'
        near(row.raw_target, raw[j], 'policy raw target', 1e-12)
        near(row.requested_target, expected_w, 'policy requested target', 1e-12)
        near(np.nan if row.sizing_sigma is None else row.sizing_sigma, volatility[j], 'policy sigma', 1e-12)
        require(row.blocked_before == before and row.blocked_after_decision == blocked, 'policy decision latch')
        require(row.block_release == release and bool(row.decision_blocked) == waiting, 'policy release/wait metadata')
        require(row.decision_reason == reason, 'policy decision reason')
        require(row.policy_sizing == ('daily' if arm in ('A10', 'A11') else 'saved'), 'sizing identity')
        require(row.policy_reentry == ('new_target_episode' if arm in ('A01', 'A11') else 'immediate'), 'reentry identity')
        expected_weights.append(expected_w)
        if w[j] != 0 and (last_w == 0 or np.sign(w[j]) != np.sign(last_w)):
            anchor = float(targets.Close.iloc[j])
        expected_anchors.append(anchor if anchor > 0 else np.nan)
        price_stop = False
        mark = float(targets.Close.iloc[j+1])
        if w[j] != 0 and anchor > 0:
            stop_level = anchor * (.97 if w[j] > 0 else 1.03)
            price_stop = bool(targets.Low.iloc[j+1] <= stop_level if w[j] > 0
                              else targets.High.iloc[j+1] >= stop_level)
            if price_stop:
                mark = stop_level
        expected_marks.append(mark)
        require(bool(row.halted_before) == halted, 'halt continuity')
        require(bool(row.price_stop_hit) == price_stop, 'price stop anchor and trigger')
        require(bool(row.stop_outside_envelope) == bool(price_stop and not
            targets.Low.iloc[j+1] <= mark <= targets.High.iloc[j+1]), 'fill envelope')
        peak = max(peak, pre_exit[j])
        portfolio_stop = bool((peak - pre_exit[j]) / peak >= .15)
        require(bool(row.portfolio_stop_hit) == portfolio_stop, 'pre-exit halt')
        require(bool(exits[j]) == bool((price_stop or portfolio_stop) and marked[j] != 0), 'required executed exit')
        peak = max(peak, after[j])
        halted = halted or (peak - after[j]) / peak >= .15
        require(bool(row.halted_after) == halted, 'post-exit halt')
        if exits[j]:
            require(price_stop or row.portfolio_stop_hit, 'registered exit cause')
            last_w, anchor = 0., 0.
            if price_stop and arm in ('A01', 'A11'):
                blocked = int(np.sign(w[j]))
        else:
            last_w = w[j]
        require(row.blocked_after == blocked, 'policy end-of-bar latch')
        require(row.stopped_direction == (int(np.sign(w[j])) if price_stop and exits[j] else 0), 'executed stopped direction')
    near(w, expected_weights, 'registered target policy', 1e-12)
    near(trace.mark_price, expected_marks, 'price marks', 1e-12)
    near(trace.entry_price, expected_anchors, 'persistent entry anchor', 1e-12)
    near(r, np.asarray(expected_marks) / targets.Close.to_numpy()[:-1] - 1, 'effective simple mark returns', 1e-12)
    active = w != 0
    if arm in ('A10', 'A11'):
        require((abs(w[active]) * volatility[active] <= .15 + 1e-12).all(), 'daily nominal risk cap')
    halted_mask = trace.halted_before.to_numpy(bool)
    near(trace.loc[halted_mask, ['exposure', 'net_return', 'fee_dollars', 'impact_dollars', 'closing_notional']],
         np.zeros((int(halted_mask.sum()), 5)), 'full-clock halted cash')
    COUNTS['traces'] += 1


def check_control(frame, original):
    require(len(frame) == len(original), 'control rows')
    for col in original:
        require(col in frame, 'control column: ' + col)
        if col.lower() == 'date':
            require(dates(frame[col]).equals(dates(original[col])), 'control dates')
        elif pd.api.types.is_bool_dtype(original[col]):
            require(np.array_equal(frame[col], original[col]), 'control flags: ' + col)
        elif pd.api.types.is_numeric_dtype(original[col]):
            atol = 1e-12 if col in ('target_position', 'exposure', 'net_return', 'mark_return',
                                  'bitcoin', 'ethereum', 'index_return') else 1e-9
            near(frame[col], original[col], 'control: ' + col, atol)
        else:
            require(frame[col].fillna('__NULL__').equals(original[col].fillna('__NULL__')),
                    'control categories: ' + col)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_metrics(record, values):
    values = np.asarray(values, float)
    equity = np.r_[1., np.cumprod(1 + values)]
    sd = values.std(ddof=1)
    expected = dict(n_bars=len(values), mean_return=values.mean(), annual_mean=365 * values.mean(),
        annual_volatility=np.sqrt(365) * sd, total_return=equity[-1] - 1,
        max_drawdown=np.min(equity / np.maximum.accumulate(equity) - 1))
    for field, number in expected.items():
        near(record[field], number, 'metric ' + field, 1e-12)
    if sd > 0:
        near(record['sharpe'], np.sqrt(365) * values.mean() / sd, 'metric Sharpe', 1e-12)
    else:
        require(record['sharpe'] is None and record['sharpe_reason'] == 'zero_variance', 'undefined Sharpe retained')


def check_periods(record, frame, column):
    expected_periods = [('2021-11-08', '2022-12-31'), ('2023-01-01', '2024-12-31'),
                        ('2025-01-01', '2025-03-31')]
    require([(p['start'], p['end']) for p in record['periods']] == expected_periods, 'three ordered periods')
    for period in record['periods']:
        clock = dates(frame.index)
        mask = (clock >= pd.Timestamp(period['start'])) & (clock <= pd.Timestamp(period['end']))
        require(clock[mask].equals(pd.date_range(period['start'], period['end'])), 'complete period calendar')
        check_metrics(period['metrics'], frame.loc[mask, column])


def flatten_cell(cell):
    primary = cell['metrics']['variants']['primary']
    fields = ('mean_return', 'annual_mean', 'annual_volatility', 'sharpe', 'total_return', 'max_drawdown')
    output = {'index.' + f: primary['index'].get('metrics', {}).get(f) for f in fields}
    for coin in ('bitcoin', 'ethereum'):
        sleeve = primary['sleeves'][coin]
        d = sleeve.get('diagnostics', {})
        for f in fields:
            output[coin + '.' + f] = sleeve.get('metrics', {}).get(f)
        for f in ('active_rows', 'waiting_rows', 'halted_cash_rows', 'other_flat_rows', 'blocked_reentry_opportunities',
                  'price_stops', 'stop_fills_outside_envelope', 'turnover_dollars'):
            output[coin + '.' + f] = d.get(f)
        for f in ('gross_dollars', 'funding_dollars', 'fee_dollars', 'impact_dollars', 'net_dollars'):
            output[coin + '.' + f] = d.get('components', {}).get(f)
        for label in ('latent', 'incoming', 'applied', 'closing'):
            for f in ('integrated_absolute', 'integrated_signed'):
                output[f'{coin}.{label}.{f}'] = d.get('exposures', {}).get(label, {}).get(f)
            for f in ('median', 'p90', 'p99', 'maximum'):
                output[f'{coin}.{label}.risk_{f}'] = d.get('risk_distributions', {}).get(label, {}).get(f)
            for f in ('above_reference', 'above_nominal_budget', 'above_leverage_cap'):
                output[f'{coin}.{label}.{f}'] = d.get('risk_counts', {}).get(label, {}).get(f)
    return output


def check_contrasts(result, gate):
    cells = {c['id']: c for c in result['cells']}
    flat = {key: flatten_cell(cell) for key, cell in cells.items()}
    direct_expected = [(c['name'], a) for c in gate['configurations'] for a in ('A10', 'A01', 'A11')]
    factorial_expected = [(c['name'], e) for c in gate['configurations'] for e in ('sizing', 'waiting', 'interaction')]
    require([(c['configuration'], c['arm']) for c in result['direct_contrasts']] == direct_expected, 'direct identities/order')
    require([(c['configuration'], c['effect']) for c in result['factorial_contrasts']] == factorial_expected, 'factorial identities/order')
    for records, factorial in [(result['direct_contrasts'], False), (result['factorial_contrasts'], True)]:
        for item in records:
            name = item['configuration']
            if factorial:
                weights = {'sizing': {'A00': -.5, 'A10': .5, 'A01': -.5, 'A11': .5},
                           'waiting': {'A00': -.5, 'A10': -.5, 'A01': .5, 'A11': .5},
                           'interaction': {'A00': 1., 'A10': -1., 'A01': -1., 'A11': 1.}}[item['effect']]
            else:
                require(item['control'] == 'A00', 'direct control identity')
                weights = {'A00': -1., item['arm']: 1.}
            complete = all(cells[name + '|' + a]['metrics']['variants']['primary']['status'] == 'complete' for a in weights)
            require(item['status'] == ('complete' if complete else 'unavailable'), 'contrast availability')
            require(set(item['differences']) == set(flat[name + '|A00']), 'contrast metric coverage')
            for field, value in item['differences'].items():
                values = [flat[name + '|' + a][field] for a in weights]
                if any(v is None for v in values):
                    require(value is None, 'null contrast preserved')
                else:
                    near(value, sum(flat[name + '|' + a][field] * coef for a, coef in weights.items()), 'contrast ' + field, 1e-9)


def main():
    gate = json.loads((ROOT / 'data/predlab/gates.json').read_text())[KEY]
    out = ROOT / gate['output_dir']
    result = json.loads((out / 'result.json').read_text())
    require(result['registered_gate'] == gate, 'result gate matches registration')
    require(set(result['output_sha256']) == {p.name for p in out.iterdir() if p.is_file() and p.name != 'result.json'}, 'every saved output is hashed')
    for name, digest in gate['pinned_files'].items():
        require(sha(ROOT / name) == digest, 'registered input: ' + name)
    for name, digest in result['output_sha256'].items():
        require(sha(out / name) == digest, 'output hash: ' + name)
    require([c['id'] for c in result['cells']] == [c['id'] for c in gate['cells']], '72 ordered identities')
    for record, registered in zip(result['cells'], gate['cells']):
        require(all(record[k] == v for k, v in registered.items()), 'complete cell identity')
    receipt = (out / 'prepared-ledger.jsonl').read_bytes()
    ledger = (ROOT / gate['financial_ledger']['path']).read_bytes()
    require(ledger == ledger[:gate['financial_ledger']['prefix_bytes']] + receipt, 'central ledger receipt')
    require(hashlib.sha256(ledger[:gate['financial_ledger']['prefix_bytes']]).hexdigest() == gate['financial_ledger']['prefix_sha256'], 'central original prefix')
    rows = [json.loads(line) for line in receipt.splitlines()]
    require(len(rows) == 72, '72 ledger rows')
    for row, cell in zip(rows, result['cells']):
        require(row['cell'] == cell['id'] and row['metrics'] == cell['metrics'], 'ledger records exact results')
    unavailable = []
    original = ROOT / 'data/factor-correction/2026-09-10/results'
    for cell in result['cells']:
        name, arm = cell['configuration']['name'], cell['arm']
        require(set(cell['metrics']['variants']) == set(gate['variants']), 'four variant identities')
        primary = {}
        for variant in gate['variants']:
            record = cell['metrics']['variants'][variant]
            require(set(record['sleeves']) == set(gate['coins']), 'two sleeve identities')
            costs = dict(gate['costs'])
            if variant in ('zero_execution', 'double_execution'):
                for k in ('fee_rate', 'slippage', 'spread', 'price_impact'):
                    costs[k] *= 0 if variant == 'zero_execution' else 2
            if variant == 'zero_funding':
                costs['funding_rate'] = 0.
            frame_path = out / f'{name}-{arm}-{variant}-returns.parquet'
            frame = pd.read_parquet(frame_path) if frame_path.exists() else None
            if frame is not None:
                require(dates(frame.index).equals(pd.date_range('2021-11-08', '2025-03-31')), 'return dates')
                require(list(frame.columns) == ['bitcoin', 'ethereum', 'index_return'], 'return columns')
                COUNTS['return_frames'] += 1
            sleeve_arrays = []
            for coin in gate['coins']:
                sleeve = record['sleeves'][coin]
                if sleeve['status'] != 'complete':
                    unavailable.append([cell['id'], variant, coin, sleeve.get('reason')])
                    require(bool(sleeve.get('reason')), 'unavailable sleeve reason')
                    if frame is not None:
                        require(frame[coin].isna().all(), 'unavailable sleeve has no manufactured returns')
                    continue
                require(frame is not None, 'complete sleeve return frame')
                trace = pd.read_parquet(out / f'{name}-{arm}-{variant}-{coin}-trace.parquet')
                targets = pd.read_parquet(original / f'{name}-{coin}-targets.parquet')
                check_trace(trace, targets, arm, costs)
                r = trace.nav_after.to_numpy() / trace.nav_before.to_numpy() - 1
                near(frame[coin], r, 'saved sleeve returns', 1e-12)
                check_metrics(sleeve['metrics'], r)
                check_periods(sleeve, frame, coin)
                d = sleeve['diagnostics']
                require(d['active_rows'] == int((trace.exposure != 0).sum()), 'active denominator')
                require(d['halted_cash_rows'] == int(trace.halted_before.sum()), 'cash denominator')
                require(d['waiting_rows'] == int(trace.decision_blocked.sum()), 'waiting denominator')
                require(d['price_stops'] == int(trace.price_stop_hit.sum()), 'stop denominator')
                near(d['exposures']['applied']['integrated_absolute'], abs(trace.exposure).sum(), 'integrated exposure')
                for field in ('gross_dollars', 'funding_dollars', 'fee_dollars', 'impact_dollars'):
                    near(d['components'][field], trace[field].sum(), 'component summary ' + field)
                sleeve_arrays.append(r)
                if variant == 'primary':
                    primary[coin] = trace
                if arm == 'A00':
                    check_control(trace, pd.read_parquet(original / f'{name}-{variant}-{coin}-trace.parquet'))
                    COUNTS['control_traces'] += 1
            if len(sleeve_arrays) == 2:
                near(frame.index_return, np.mean(sleeve_arrays, axis=0), 'separate sleeve index', 1e-12)
                check_metrics(record['index']['metrics'], frame.index_return)
                check_periods(record['index'], frame, 'index_return')
                if arm == 'A00':
                    oldframe = pd.read_parquet(original / f'{name}-{variant}-returns.parquet')
                    require(dates(frame.index).equals(dates(oldframe.index)), 'control return index')
                    check_control(frame.reset_index(drop=True), oldframe.reset_index(drop=True))
                    COUNTS['control_return_frames'] += 1
            elif frame is not None:
                require(frame.index_return.isna().all(), 'missing sleeve makes index unavailable')
        shadow_record = cell['metrics']['log_shadow']
        if shadow_record['status'] == 'complete':
            shadow = pd.read_parquet(out / f'{name}-{arm}-invalid-log-shadow.parquet')
            require(dates(shadow.index).equals(pd.date_range('2021-11-08', '2025-03-31')), 'shadow dates')
            expected = []
            for coin in gate['coins']:
                tr = primary[coin]
                r = tr.nav_after.to_numpy() / tr.nav_before.to_numpy() - 1
                invalid = r + tr.exposure.to_numpy() * (np.log1p(tr.mark_return) - tr.mark_return).to_numpy()
                near(shadow[coin], invalid, 'fixed invalid log shadow', 1e-12)
                expected.append(invalid)
            near(shadow.index_return, np.mean(expected, axis=0), 'shadow index', 1e-12)
            check_metrics(shadow_record['index']['metrics'], shadow.index_return)
            COUNTS['shadows'] += 1
        else:
            unavailable.append([cell['id'], 'invalid-log-shadow', shadow_record.get('reason')])
    require(len(result['direct_contrasts']) == 54, '54 direct contrasts')
    require(len(result['factorial_contrasts']) == 54, '54 descriptive factorial effects')
    check_contrasts(result, gate)
    review = dict(status='pass', independent_of_runner_and_controller=True,
        result_sha256=sha(out / 'result.json'), counts=COUNTS, unavailable=unavailable,
        checks='Pinned hashes, all saved control fields, complete clocks, independent causal sigma and target/stop-block transitions, unchanged stop anchors and fills, every simple-PnL/funding/fee/impact/turnover leg, NAV and pre/post-exit absorbing halt identities, return-index arithmetic, frozen invalid-log shadows and full denominators. No financial replay.')
    path = Path(__file__).with_name('result-review.json')
    with path.open('x') as handle:
        json.dump(review, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(review, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
