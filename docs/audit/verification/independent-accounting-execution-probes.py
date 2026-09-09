"""Offline review probes; use only fixtures and temporary storage."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib
import json
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests' / 'predlab'))
sys.path.insert(0, str(ROOT / 'scripts'))
import test_execution_repair as fixtures
from tradingagents.predlab.features import oi_features

results = {}
with tempfile.TemporaryDirectory() as temp, pytest.MonkeyPatch.context() as monkey:
    mod, row = fixtures.live.__wrapped__(Path(temp), monkey)
    exchange = fixtures.Exchange(reject={'BBBUSDT'})
    results['first_partial_batch'] = mod.run(exchange, False)
    exchange.reject.clear()
    later = fixtures.NOW + timedelta(minutes=11)
    class LaterClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return later
    monkey.setattr(mod, 'datetime', LaterClock)
    exchange.quote_time = int(later.timestamp() * 1000)
    results['retry_11min_later_with_fresh_exchange_quote'] = mod.run(exchange, False)
    results['retry_positions'] = exchange.positions()
    results['retry_original_target'] = fixtures.latest(mod)['target_qty']

with tempfile.TemporaryDirectory() as temp, pytest.MonkeyPatch.context() as monkey:
    mod, row = fixtures.live.__wrapped__(Path(temp), monkey)
    exchange = fixtures.Exchange()
    exchange.user_trades = lambda *args: [{'commissionAsset': 'USDT', 'commission': '0.01'}]
    intent = {'asof': row['asof'], 'symbol': 'AAAUSDT', 'side': 'BUY', 'qty': 10,
              'reduce_only': False, 'client_order_id': 'partial-cancel'}
    mod._observe(exchange, intent, {'orderId': 1, 'status': 'CANCELED', 'executedQty': '5',
                                    'avgPrice': '2', 'cumQuote': '10'})
    full = {**intent, 'symbol': 'BBBUSDT', 'side': 'SELL', 'client_order_id': 'full-fill'}
    mod._observe(exchange, full, {'orderId': 2, 'status': 'FILLED', 'executedQty': '10',
                                  'avgPrice': '10', 'cumQuote': '100'})
    results['partial_cancel_compare'] = mod.compare()
    report = json.loads((mod.LDIR / 'compare_report.json').read_text())
    results['partial_cancel_fill_records'] = len(mod._rows(mod.FILLS))
    results['partial_cancel_fee_coverage'] = report['fee_coverage']
    results['partial_cancel_reported_fees'] = report['total_fees_usdt']

index = pd.date_range('2021-01-01', periods=24, freq='5min', tz='UTC')
raw = pd.DataFrame({'oi': 100., 'top_ls_positions': np.nan, 'ls_accounts': np.nan,
                    'taker_ls_vol': np.nan}, index=index)
raw.loc[index[0], 'top_ls_positions'] = 1.1
raw.loc[index[6], 'ls_accounts'] = 1.2
raw.loc[index[11], 'taker_ls_vol'] = 1.3
out = oi_features(raw, '1h')
results['oi_single_nonnull_field_observation_accepted'] = out.iloc[1][['top_ls_lag1','ls_acct_lag1','taker_ls_lag1']].to_dict()
results['oi_source_field_timestamps'] = {c: str(raw[c].first_valid_index())
    for c in ['top_ls_positions','ls_accounts','taker_ls_vol']}
print(json.dumps(results, indent=2))
