"""Read-only actual-history admission-cost proof; no financial-value parsing.

Run once under resource_guard_v2.py. Writes only an exclusive engineering report.
Does not create a claim, recompute economics, read credentials or use networking.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tradingagents.research_options_capture.control import inventory


def main():
    report=Path(__file__).with_name('options-actual-history-preflight-result.json')
    paths=sorted((ROOT/'research_runs').glob('*/claim.json'))
    before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if len(before)!=19:raise ValueError('expected retained nineteen-claim boundary')
    started=time.monotonic()
    with report.open('x') as output:
        items,_=inventory(ROOT)
        after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        if before!=after:raise ValueError('claim bytes changed during proof')
        result={'scope':'Actual nineteen-history structural hashes only; no economic recomputation or empirical attempt.',
                'elapsed_seconds':time.monotonic()-started,'claims':items,
                'complete':sum(v['terminal']=='complete.json' for v in items.values()),
                'failed':sum(v['terminal']=='failed.json' for v in items.values()),'pass':True}
        json.dump(result,output,sort_keys=True,indent=2);output.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='claims'}))


if __name__=='__main__':main()
