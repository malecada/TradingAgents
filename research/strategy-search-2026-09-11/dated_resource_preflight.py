"""Invented complete pipeline under exact corrected resource wrapper; no real data."""
import runpy
import math
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
fixture = runpy.run_path('tests/research/test_dated_book_run.py')
inputs = fixture['synthetic_inputs']()
# Two distinct invented market paths force the complete OLS/HAC path.
for record in inputs[2]['requests']:
    if record.get('kind') == 'spot':
        btc = record['id'] == 'btc-spot'
        start = fixture['runner'].archive.capture_module.START_MS
        day = 86400000
        rows = []
        for i in range(91):
            price = 100 + (math.sin(i*.47) if btc else math.cos(i*.31))*2 + i*.01
            rows.append([start+i*day, price, price, price, price, 1, start+(i+1)*day-1, 100, 1, .5, 50, 0])
        record.update(fixture['receipt'](record, json.dumps(rows).encode()))
books, summary, cells = fixture['runner'].evaluate(*inputs)
assert len(cells) == 8 and all(row['status'] == 'complete' for row in cells)
assert all(row['statistics']['expected_return_confidence']['status']=='unavailable' for row in summary['cases'])
assert all(row['statistics']['market_exposure']['status']=='complete' for row in summary['cases'])
print('PASS: eight invented books using the real statistics dependency under corrected resource guard.')
