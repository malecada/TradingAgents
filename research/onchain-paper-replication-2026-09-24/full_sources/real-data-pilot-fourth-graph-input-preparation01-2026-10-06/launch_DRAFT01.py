"""One-use entry into the existing genuine graph supervisor, with outer exit."""
import json
import subprocess
from preflight_DRAFT01 import ROOT,HERE,check
from tradingagents.research.onchain_replication.job import _command


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush()
        import os
        os.fsync(stream.fileno())


if __name__=='__main__':
    args,preflight=check()
    write(HERE/'launch-attempt01.json',preflight)
    code=None
    try:
        code=subprocess.call(_command(args,'launch'),cwd=ROOT)
    finally:
        write(HERE/'outer-exit01.json',{'experiment':args.experiment,'source':args.source,
            'exit_code':code,'qualification':'Actual parent return code; null remains unknown if the call did not return. One-use namespace remains reserved.'})
    raise SystemExit(code)
