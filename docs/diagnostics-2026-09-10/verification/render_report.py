"""Render saved diagnostic summaries only; never rerun inference or a strategy."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/diagnostics-2026-09-10/RESULTS.md'


def read(family):
    path = ROOT / f'data/diagnostics/2026-09-10/{family}/result.json'
    return json.loads(path.read_text()), hashlib.sha256(path.read_bytes()).hexdigest()


def pct(x):
    return f'{100*x:.2f}%'


def render():
    f, fhash = read('forecast')
    r, rhash = read('risk')
    assert f['available_cells'] == 16 and r['counts']['complete_sleeves'] == 36
    assert f['git_commit'] == r['git_commit']
    lines = [
        '# Saved forecast reliability and factor risk diagnostics — September 10, 2026',
        '',
        '**All sixteen forecast comparisons and thirty-six factor sleeves are complete.** '
        'Volume prediction retains a consistent historical improvement over seasonal baselines. '
        'The factor traces expose stale sizing and repeated stop/re-entry behavior that warrants a narrowly defined risk-policy investigation. '
        '**Zero strategies are validated.** No trading rule, model, original gate or holdout result was changed.',
        '',
        '## Scope and reproducibility',
        '',
        'The two charters and exact input hashes were registered at `38d9a67e6ff042cb1fd870877b3e0222f40fdc08` before implementation or results. '
        f'The reviewed executable source was committed as `{f["git_commit"]}` before both successful, single executions. '
        'The existing saved development artifacts end March 31, 2025. No fitting, strategy replay, new data, network request, paid purchase or holdout read occurred. '
        'The 22 settlement-blocked cases remain deferred.',
        '',
        '| Evidence | Identity |', '|---|---|',
        f'| [Forecast result](../../data/diagnostics/2026-09-10/forecast/result.json) | SHA-256 `{fhash}` |',
        f'| [Risk result](../../data/diagnostics/2026-09-10/risk/result.json) | SHA-256 `{rhash}` |',
        '| [Forecast charter](forecast-charter.md) | `audit_saved_forecast_inference_2026_09_10`; 16 cells, 35 pins |',
        '| [Factor charter](factor-risk-charter.md) | `audit_factor_risk_2026_09_10`; 18 configurations × 2 assets, 78 pins |',
        '',
        'The runners record all 52 identities in separate forensic ledgers. The original financial ledger remains at 748 rows, 569,325 bytes and SHA-256 '
        '`4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. '
        'Source reviews and final test logs are retained under `verification/`: 57 forecast tests and 80 factor tests passed before execution. '
        'The [independent result review](verification/result-review.md) and [final preservation record](verification/preservation-final.json) provide completion checks.',
        '',
        '## Forecast reliability',
        '',
        'Positive percentages below mean lower forecast loss than the declared baseline, not an investment return. '
        'Return uses squared error against zero; direction uses Brier loss against the base rate; variance uses normalized QLIKE against HAR; '
        'volume uses absolute error on log volume against seasonal naive. The original common MASE scale cancels from the volume ratios. '
        'Every scalar comparison reconciles with the prior correction.',
        '',
        'The fixed circular stationary bootstrap uses 2,000 draws, 21-day mean blocks and seed 20260910 independently per cell. '
        'All 32,000 saved draws have valid denominators. Full physical calendars and fallback observations are retained: '
        'the unavailable October 28, 2024 20:00 UTC hour remains unscoreable in both hourly variance and volume comparisons. '
        'It is not replaced with a fabricated target or silently removed from bootstrap time.',
        '',
        '| Asset | Grid | Target | Relative loss improvement | Conditional 95% interval | Eligible Holm p | Stable periods descriptor |',
        '|---|---|---|---:|---:|---:|---|',
    ]
    names = {'T1_ret':'Return', 'T2_dir':'Direction', 'T3_rv':'Variance', 'T4_vol':'Volume'}
    for c in f['cells']:
        symbol, grid, target = c['cell'].split('|')
        b = c['bootstrap']; ci = b['relative_improvement_ci']
        holm = 'unavailable' if c['holm_adjusted_p'] is None else f'{c["holm_adjusted_p"]:.6f}'
        lines.append(f'| {symbol.removesuffix("USDT")} | {grid} | {names[target]} | {pct(b["relative_improvement"])} | '
                     f'[{pct(ci[0])}, {pct(ci[1])}] | {holm} | {"met" if c["historical_stability_descriptor"] else "not met"} |')
    lines += [
        '',
        '**Volume is the most consistent forecast finding.** All four volume comparisons meet the original 5% effect descriptor, '
        'improve in each of the three fixed historical periods, and retain Holm-adjusted p=0.007996 across the full 16-slot family. '
        'Raw valid prediction coverage is 92.85–97.45%; fallback observations remain included. '
        'These are conditional comparisons of saved forecasts against seasonal naive. '
        'They do not resolve historical model selection, prove stationarity or establish that ENet is the best model. '
        'Earlier saved LightGBM scalar losses were lower; no new competitor comparison or coverage-parity claim was made.',
        '',
        '**Directional alpha is not established.** Every mean-return comparison has worse point loss than its zero baseline. '
        'Hourly direction accuracy edges are 1.7768 percentage points for BTC and 1.9119 for ETH, below the original 2-point floor; '
        'their Brier-loss intervals cross zero improvement. Point AUCs are 0.5314 and 0.5344, but the required AUC interval is absent. '
        'Daily direction is worse than its baseline. ETH hourly variance has a favorable conditional interval, while daily ETH variance is uncertain and BTC variance is worse.',
        '',
        'Formal primary inference for return, direction and variance remains unavailable because applicability of nested-model tests to these penalized, '
        'selected, expanding estimates is unresolved. Those twelve slots enter Holm as one; their conditional intervals do not reverse the original gates. '
        'The stability descriptor means positive loss differential in at least two of three fixed periods, with at least thirty observations per period. '
        'It is descriptive historical evidence, not fresh validation.',
        '',
        '## What the factor traces establish',
        '',
        'All 36 sleeves reconcile to the saved accounting: 44,640 daily rows, including 8,873 dates with nonzero applied exposure. '
        'The sizing formula sets an entry risk proxy of at most 15% (`0.10 × 0.5 × 3`), subject to the leverage cap. '
        'Size is then retained until a raw-target entry or flip. This is entry-time volatility sizing; it does not continuously maintain that risk level. '
        'The diagnostic proxy is absolute position weight multiplied by trailing annualized volatility, not realized account volatility.',
        '',
        'The applied proxy exceeds its entry reference on 4,458/8,873 active sleeve-dates (50.24%). '
        'The 95th-percentile volatility gate is closed on 939 active sleeve-dates; that gate controls builder entries/flips and does not flatten an existing target. '
        'No applied or latent target breaches the 3× leverage cap. '
        'Counts across configurations describe overlapping sleeve-date observations, not independent experiments or a pooled account.',
        '',
        'Of 852 recorded price stops, 726 are followed by same-direction next-day re-entry, all reusing the saved sizing reference; '
        '93 are followed by opposite-direction entry, 25 by permanent halt, and 8 by a flat date. '
        'Thus 819/852 stops are followed by immediate renewed exposure. '
        'A price stop closes the executed position while the target builder can continue holding its old directional target and size.',
        '',
        'The following two configurations were already discussed before this diagnostic; their appearance here is explanatory, not a new selection rule.',
        '',
        '| Configuration / asset | Active dates | Applied risk p90 / maximum | Dates above entry reference | Same-direction re-entry / stops | Maximum reused sizing age at re-entry |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for c in r['cells']:
        if c['configuration']['name'] not in ('tsmom_k30_ls','macross_10_50_ls'):
            continue
        s = c['summary']; d = s['risk_distributions']['applied']
        age = s['stop_sizing_age_distributions']['reused_reference_reentry']['maximum']
        lines.append(f'| `{c["id"].replace("|", " / ")}` | {d["active_rows"]} | {pct(d["p90"])} / {pct(d["maximum"])} | '
                     f'{s["counts"]["above_reference_risk"]}/{d["active_rows"]} | '
                     f'{s["stop_successors"].get("same_sign_reentry",0)}/{s["price_stops"]} | {age:.0f} days |')
    lines += [
        '',
        'All 36 sleeves eventually trip the permanent 15% drawdown latch. In 35 sleeves the threshold is crossed before final exit charges; '
        'only ETH 30-day momentum first crosses afterward, from 14.999356% to 15.032114%. '
        'The gross market component dominates the peak-to-halt loss in the four examples above. '
        'A fee crossing at the boundary is an accounting observation, not proof that removing the fee would improve the full path.',
        '',
        'Maintenance turnover is real even when the target weight is unchanged, because holdings and NAV drift. '
        'The signed target-change and maintenance components reconcile after retaining their netting term; their absolute values are not additive trade volume. '
        'Linear execution charges include the saved fee/slippage/spread assumption, with impact recorded separately. '
        'Stop-successor entry charges are a subset of opening charges, so they must not be added a second time. '
        'The detailed [risk interpretation](verification/risk-interpretation.md) reports sleeve-specific dollars and disjoint charge categories.',
        '',
        '**Cash-tail count addendum:** the earlier factor report stated 238–1,157 days. The preserved traces establish 238–1,158 '
        'already-halted cash dates. ETH 180-day long/short momentum halts on January 28, 2022; January 29, 2022 through March 31, 2025 contains 1,158 dates. '
        'This corrects the earlier prose only. Its original halt date, return series, metrics and files remain unchanged.',
        '',
        '## Next research decision',
        '',
        'The clearest engineering follow-up is to specify a consistent contract between signal persistence, current volatility sizing and execution stop state. '
        'A bounded future comparison could test refreshing size when exposure is maintained or reopened, while preserving the signal and accounting conventions. '
        'The exact alternative, comparison set, costs and fresh validation route must be registered before any new performance calculation. '
        'The present observations do not determine the best resizing cadence, justify removing a halt, or show that a changed rule will make a lead pass. '
        'Lower Kelly sizing and removal of volatility targeting already appear in the historical record and should not be represented as new discoveries.',
        '',
        'Volume forecasts warrant retention as inputs for a narrowly specified execution-cost investigation. '
        'The earlier day-start execution-profile test did not establish useful economic savings; a lower volume prediction error alone does not establish them either. '
        'A causal mapping from forecast to actual order schedule, with an executable cost comparison, would be a separate registered experiment. '
        'Mean-return tuning is not supported by these results. ETH variance retains qualified descriptive evidence but no new formal validation.',
        '',
        'Original price-cache provenance, assumed daily funding, threshold stop fills and the separate BTC/ETH sleeve-index construction remain limitations. '
        'The spent holdouts stay spent, and the deferred settlement cases are unchanged. '
        'These findings provide specific questions for further research; they do not promote a strategy.',
        '',
        '## Complete factor denominator',
        '',
        '| Configuration / asset | Active dates | Applied risk p90 | Applied risk maximum | Price stops | First halt | Crossing stage |',
        '|---|---:|---:|---:|---:|---|---|',
    ]
    for c in r['cells']:
        s=c['summary']; d=s['risk_distributions']['applied']; h=s['first_halt']
        lines.append(f'| `{c["id"].replace("|", " / ")}` | {d["active_rows"]} | {pct(d["p90"])} | {pct(d["maximum"])} | '
                     f'{s["price_stops"]} | {h["date"][:10]} | {h["crossing_stage"]} |')
    lines += ['', 'Every row is a qualified completed diagnostic. Full dated exposures, flags, charge identities, risk denominators and stop events are retained in the immutable Parquets.', '']
    with OUT.open('x') as stream:
        stream.write('\n'.join(lines))


if __name__ == '__main__':
    render()
