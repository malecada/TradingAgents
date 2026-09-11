"""Exact transport/journal groups using invented child frames, no network.

The standard outer guard measures aggregate descendant RSS. Fake children also
have PDEATHSIG, matching the production child's parent-death contract. This is
not a complete calendar, history-plus-capture, deployment or real latency proof.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('fixture',ROOT/'tests/research/test_options_capture_transport.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)


def main():
    out=Path(__file__).with_name('options-transport-resource-result.json')
    groups=[]
    with out.open('x') as report:
        for label,count,cap in [('routine',16,8192),('maximum-initial-metadata',3,5*1024**2)]:
            directory=Path(tempfile.mkdtemp(prefix='options-transport-'+label+'-'))
            path,args,now,deadline=fixture.setup(directory,count=count,cap=cap)
            started=time.monotonic()
            with fixture.Journal(path,**args) as j:
                j.begin_group(list(j.slots),now_ms=now)
                result=fixture.collect(j,deadline,'ok')
                all_available=all(m['body_complete'] and m['clock_consistent'] and m['within_controller_deadline'] for m in result['sources'].values())
                acquisition_seconds=time.monotonic()-started
                seal=j.seal('complete')
            elapsed=time.monotonic()-started
            files=[p for p in path.iterdir() if p.is_file()]
            groups.append({'group':label,'source_count':count,'body_cap':cap,'all_available':all_available,
                           'acquisition_seconds':acquisition_seconds,'invocation_seconds':elapsed,
                           'journal_files':len(files),'journal_bytes':sum(p.stat().st_size for p in files),
                           'synthetic_fixture_path':str(path),'seal_sha256':hashlib.sha256((path/'seal.json').read_bytes()).hexdigest()})
        value={'scope':__doc__,'groups':groups,'pass':all(g['all_available'] for g in groups),
               'transport_sha256':hashlib.sha256((ROOT/'tradingagents/research_options_capture/transport.py').read_bytes()).hexdigest(),
               'fixture_sha256':hashlib.sha256((ROOT/'tests/research/test_options_capture_transport.py').read_bytes()).hexdigest()}
        json.dump(value,report,sort_keys=True,indent=2);report.write('\n')
    print(json.dumps(value));return 0 if value['pass'] else 1


if __name__=='__main__':raise SystemExit(main())
