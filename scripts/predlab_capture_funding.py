"""Capture public current funding evidence into a new immutable directory."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tradingagents.predlab.funding_capture import capture_run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root',type=Path,required=True,
                        help='Dedicated operational capture root; never the historical funding store')
    parser.add_argument('--symbols',nargs='+',help='Explicit USDT contracts; otherwise current eligible metadata universe')
    args=parser.parse_args()
    run=args.output_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    result=capture_run(run,symbols=args.symbols,progress=lambda p: print(json.dumps(p),flush=True))
    print(json.dumps(dict(snapshot=str(run.resolve()),status=result['status'],
        requested=len(result['requested_symbols']),captured=sum(e['status']=='captured' for e in result['instruments'].values()),
        requests=len(result['requests'])),sort_keys=True),flush=True)
    return 0 if result['status']=='captured' else 2


if __name__=='__main__':
    raise SystemExit(main())
