"""Invented bounded episode exposing exact weighted-basis denominator growth."""
import importlib.util
import json
from pathlib import Path
import time

path=Path(__file__).resolve().parents[1]/'options_policy_engine.py'
spec=importlib.util.spec_from_file_location('reviewed_engine',path)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
rows=[]
for i in range(1057):
    delta=['.50000000000000000001','.50000000000000000000','.50000000000000000003','.49999999999999999999'][i%4]
    option={'unit':1,'bid':'10','ask':'10','bid_qty':'1e25','ask_qty':'1e25','mark':'10','delta':'0'}
    rows.append({'time_ms':i*3600000,'decision_available':True,'index':str(100+i%7),
        'call':dict(option,delta=delta),'put':option,
        'perp':{'bid':str(100+i%7),'ask':str(100+i%7),'bid_qty':'1e25','ask_qty':'1e25','mark':str(100+i%7)}})
started=time.monotonic()
try:
    result=engine.ledger(rows,capital='1e25',option_quantity='1e20',costs={'option_fee_rate':'0','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'},hedge_lot='1',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=[],funding_events=[])
    report={'status':'complete','bytes':len(json.dumps(result))}
except Exception as exc:
    report={'status':'exception','error':type(exc).__name__+': '+str(exc)}
report.update(seconds=time.monotonic()-started,scope='Invented1057-row input only; no actual data or empirical lifecycle.')
# A new filename preserves the original failure after source changes.
Path(__file__).with_name('options-policy-arithmetic-growth-current-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
