"""Format the retained measurement without fetching or selecting replacement observations."""
from collections import Counter
from decimal import Decimal
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path('data/carry-feasibility/2026-09-10')
DOC = Path('docs/carry-feasibility-2026-09-10')
D = Decimal


def money(value):
    return f'{D(value):.4f}'


def pct(value):
    return f'{D(value)*100:.3f}%'


def build():
    if (DOC / 'RESULTS.md').exists() or (DOC / 'screen-summary.json').exists():
        raise FileExistsError('retained reports already exist')
    manifest = json.loads((ROOT / 'capture/manifest.json').read_text())
    ledger_bytes = (ROOT / 'measurement_ledger.jsonl').read_bytes()
    if hashlib.sha256(ledger_bytes).hexdigest() != manifest['ledger_sha256']:
        raise ValueError('measurement ledger hash differs')
    actual_files = {str(path) for path in (ROOT / 'capture').rglob('*') if path.is_file() and path.name != 'manifest.json'}
    if set(manifest['files']) != actual_files:
        raise ValueError('capture file inventory differs')
    for name, digest in manifest['files'].items():
        path = Path(name)
        if not path.resolve().is_relative_to((ROOT / 'capture').resolve()):
            raise ValueError('capture evidence path escapes its directory')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('capture evidence hash differs: ' + name)
    ledger = [json.loads(line) for line in (ROOT / 'measurement_ledger.jsonl').read_text().splitlines()]
    inventory = json.loads((ROOT / 'capture/inventory.json').read_text())
    entries = json.loads((ROOT / 'capture/entries.json').read_text())
    expected_entries = {'|'.join(map(str, dimensions)) for dimensions in itertools.product(range(3), ('BTC','ETH'), ('1000','10000'), ('1','1/3'), ('1','2'))}
    expected_rows = {entry+'|'+ratio+'|'+bps for entry,ratio,bps in itertools.product(expected_entries,('0.5','1','2'),('0','10','50'))}
    if len(entries) != 48 or {e['id'] for e in entries} != expected_entries:
        raise ValueError('expected 48 unique entry identities')
    if len(ledger) != 432 or {r['measurement_id'] for r in ledger} != expected_rows:
        raise ValueError('expected 432 unique measurement identities')
    for entry in entries:
        if entry['id'] != '|'.join(str(entry[k]) for k in ('snapshot','asset','capital','reserve','fee_multiplier')):
            raise ValueError('entry identity differs from dimensions')
    for row in ledger:
        if row['measurement_id'] != '|'.join(str(row[k]) for k in ('snapshot','asset','capital','reserve','fee_multiplier','terminal_index_ratio','adverse_exit_bps')):
            raise ValueError('measurement identity differs from dimensions')
        if row['result']['status'] not in {'complete', 'unavailable'}:
            raise ValueError('invalid measurement status')
    counts = Counter(row['result']['status'] for row in ledger)
    reasons = Counter(row['result'].get('reason', '') for row in ledger if row['result']['status'] != 'complete')
    screens = []
    for asset in ('BTC', 'ETH'):
        for capital in ('1000', '10000'):
            cells = [row for row in ledger if row['asset'] == asset and row['capital'] == capital
                     and row['reserve'] == '1' and row['fee_multiplier'] == '2' and row['adverse_exit_bps'] == '10']
            complete = len(cells) == 9 and all(row['result']['status'] == 'complete' for row in cells)
            positive = complete and all(D(row['result']['net_cash_profit']) > 0 for row in cells)
            screens.append({'asset': asset, 'capital': capital, 'required_cells': 9,
                'retained_cells': len(cells), 'complete': complete, 'necessary_cash_screen_pass': positive,
                'executable_admission': False, 'strategy_validated': False})
    lines = ['# Dated BTC/ETH carry feasibility — September 10, 2026', '',
        'The current public-book measurement is complete. It is a conditional quote-to-expiry calculation, not a strategy backtest or a promise that both legs can be filled. The user specified approximately 1,000 initially and 10,000 potentially, with Binance and possibly Bitrue. Calculations use 1,000/10,000 **USDT already available on venue**; fiat conversion and stablecoin exposure are not priced.', '',
        f"Execution source: `{manifest['source_commit']}`. The fixed grid retains **{len(ledger)} scenario rows**, of which **{counts['complete']}** are calculable. All {len(entries)} entry-size cases, three scheduled snapshots, raw bodies and failures are retained. The original 820-row financial ledger is unchanged. **Zero strategies are validated.**", '',
        '## Contract inventory', '',
        'Binance selection is the earliest eligible conventional linear USDT expiry between seven and 180 days, separately for BTC and ETH. The rule never chooses the highest basis. Other eligible maturities remain in the inventory but are not alternative financial trials.', '',
        '| Asset | Selected future | Spot pair | Expiry (UTC milliseconds) |', '|---|---|---|---:|']
    selected = ((inventory.get('inventory') or {}).get('selected') or {})
    for asset in ('BTC','ETH'):
        spec = selected.get(asset)
        lines.append(f"| {asset} | {spec['future_id'] if spec else 'Unavailable'} | {spec['spot_id'] if spec else 'Unavailable'} | {spec['expiry_ms'] if spec else 'Unavailable'} |")
    lines += ['', 'Bitrue dated-product availability remains unverified. Its documented perpetual products and a URL named `delivery` do not establish an eligible expiring contract. [Official-source review](SOURCES.md).', '',
        '## Conditional entry and terminal economics', '',
        'The following table retains all three observations. Its displayed scenario uses the full futures-notional reserve, the registered base fee assumptions, a terminal settlement index equal to the initial spot ask, and spot sale at that same index. This is one fixed reference scenario; fees and sale/index alignment are not verified future outcomes. Annualization is arithmetic on the full capital budget and does not imply repeated opportunities.', '',
        '| Snapshot | Asset | Capital (USDT) | Modeled net cash (USDT) | Return on full capital | Simple annualized return |', '|---:|---|---:|---:|---:|---:|']
    for row in ledger:
        if row['reserve'] != '1' or row['fee_multiplier'] != '1' or row['terminal_index_ratio'] != '1' or row['adverse_exit_bps'] != '0':
            continue
        r=row['result']
        values=(money(r['net_cash_profit']),pct(r['net_return_on_capital']),pct(r['annualized_simple_return'])) if r['status']=='complete' else ('Unavailable',)*3
        lines.append(f"| {row['snapshot']} | {row['asset']} | {row['capital']} | {' | '.join(values)} |")
    lines += ['', '## Necessary economic screen', '',
        'The preregistered screen requires positive net cash across all three snapshots and all three terminal-index levels (half, unchanged, double), using full reserve, doubled fees and spot liquidation 10bp below the settlement index. Passing this screen only supports considering further design. It does not admit a strategy, settle the cash-benchmark question, or establish margin survival.', '',
        '| Asset | Capital (USDT) | Complete required cells | Positive in every required cell | Executable admission |', '|---|---:|---:|---|---|']
    for row in screens:
        status='Yes, conditional' if row['necessary_cash_screen_pass'] else ('No' if row['complete'] else 'Unavailable')
        lines.append(f"| {row['asset']} | {row['capital']} | {'9/9' if row['complete'] else 'Unavailable'} | {status} | No |")
    lines += ['', '## Complete sensitivities and limitations', '',
        'The [measurement ledger](../../data/carry-feasibility/2026-09-10/measurement_ledger.jsonl) contains every terminal-price, 0/10/50bp adverse-exit, base/double-fee and full/one-third-reserve case. Each row reports net cash separately from illustrative 0%, 3% and 5% annual cash benchmarks on the same full capital and exact holding period. These benchmark rates are sensitivity assumptions, not observed available deposit yields or a retrospectively chosen hurdle.', '',
        'Future bid proceeds are not credited at entry. Spot principal, entry fees and total futures reserve must fit inside the stated budget. Spot base commission is deducted before measuring the hedge, with lot rounding and the small residual explicitly retained. Capital efficiency from a one-third reserve is not a risk reduction. A positive terminal payoff can coexist with an earlier collateral shortfall.', '',
        'Public depth is neither simultaneous execution nor demonstrated fills. Spot responses lacking an event timestamp cannot prove freshness. Future timestamps, request spans and clock uncertainty are checked; failures remain unavailable. Exact current account fees, fee rounding, contract/entity applicability, settlement fee basis, maintenance margin and transfer constraints are still unverified. The modeled absolute-notional expiry fee is not substituted for the ambiguous official legal expression. [Sources and applicability gaps](SOURCES.md).', '',
        '## Next stage admission', '',
        'A separately registered strategy evaluation can start only after actual product access, both-leg commissions and fee assets, settlement treatment, margin/liquidity behavior and the user\'s return/risk hurdle are resolved. Reuse the synthetic quantity/cash tests when implementing that contract. No old holdout can be made fresh, no historical delisting record is being recovered, and no paper account or order is started by this report.', '',
        'The [pure cashflow implementation](../../scripts/carry_feasibility_math_2026_09_10.py) is deliberately separate from the derivative-only event book, which does not debit spot principal or manage cash wallets. Its hand-derived down/flat/up examples verify the arithmetic without claiming an exchange liquidation model.', '',
        '## Retained unavailable outcomes', '']
    lines += [f'- {count} rows: `{reason}`.' for reason,count in sorted(reasons.items())] or ['No scenario row is unavailable; all executable-admission qualifications above still apply.']
    (DOC / 'RESULTS.md').write_text('\n'.join(lines)+'\n')
    (DOC / 'screen-summary.json').write_text(json.dumps({'source_commit':manifest['source_commit'],'ledger_sha256':manifest['ledger_sha256'],'statuses':dict(counts),'screens':screens},indent=2)+'\n')


if __name__=='__main__':
    build()
