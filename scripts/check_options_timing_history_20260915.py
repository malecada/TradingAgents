"""Read-only actual20 preservation + independent old protocol; no new grant."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tradingagents.research_options_timing import closed_history,control


def main():
    report=ROOT/'research/strategy-search-2026-09-11/reviews/options-timing-history-preflight-20260915.json'
    if report.exists():raise SystemExit('retained report exists; refuse repeat')
    begin=time.monotonic();now=datetime.now(timezone.utc).isoformat()
    closure=json.loads((ROOT/'research/strategy-search-2026-09-11/reviews/options-actual-failure-close-20260915.json').read_bytes())
    result={'scope':'Read-only twenty actual identities and old prospective protocol reconstruction; no financial parsing, new certificate, grant or claim','checked_at':now,'pass':False}
    try:
        before,_=control.inventory(ROOT)
        if len(before)!=20 or sum(v['terminal']=='failed.json' for v in before.values())!=4:raise ValueError('expected20 identities16complete4failed')
        result['before']=before
        result['protocol']=closed_history._verify_original(root=ROOT,now_utc=now,quiescence_evidence=closure['quiescence_evidence'])
        after,_=control.inventory(ROOT)
        result['after_sha256']=hashlib.sha256(control.canonical(after)).hexdigest()
        result['before_sha256']=hashlib.sha256(control.canonical(before)).hexdigest()
        result['pass']=before==after and result['protocol']['status']=='failed'
    except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
    result['elapsed_seconds']=time.monotonic()-begin
    with report.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:result.get(k) for k in ('pass','elapsed_seconds','error')}))
    raise SystemExit(0 if result['pass'] else 1)


if __name__=='__main__':main()
