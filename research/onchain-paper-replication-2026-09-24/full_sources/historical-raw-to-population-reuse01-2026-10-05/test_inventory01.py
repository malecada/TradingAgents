"""Pure metadata controls. No lifecycle authority or real payload operations."""
import importlib.util,json,tempfile
from pathlib import Path
from datetime import date
p=Path(__file__).with_name('inventory01.py');spec=importlib.util.spec_from_file_location('inventory',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def refuses(f):
 try:f()
 except (ValueError,FileNotFoundError):return
 raise AssertionError('expected refusal')
with tempfile.TemporaryDirectory(dir=p.parent) as td:
 root=Path(td);q=root/'metadata.json';q.write_text('{}');assert m.load(q,m.sha(b'{}'))=={};refuses(lambda:m.load(q,'0'*64));checks.append('metadata hash tamper refused')
 ns,pin=m.functions();s=root/'opaque.zst';s.write_bytes(b'xxxx');blob={'path':s.name,'stored_bytes':4,'raw_bytes':8,'codec':'zstd','raw_sha256':'1'*64,'stored_sha256':'2'*64}
 assert ns['span'](blob,10,18,root)['end']==18
 refuses(lambda:ns['span'](blob,10,19,root));checks.append('half-open range framing enforced')
 s.write_bytes(b'x');refuses(lambda:ns['span'](blob,10,18,root));checks.append('stored extent mismatch refused without reading payload')
 ds=m.week_days(date(2024,1,1));assert m.full_weeks(ds)==['2024-01-01'];assert m.full_weeks(ds[:-1])==[];checks.append('partial week excluded')
assert not any(x in __import__('sys').modules for x in ('numpy','torch','pyarrow','scipy'));checks.append('no numerical imports')
v=json.loads(p.with_name('INVENTORY01.json').read_bytes());assert v['metadata_supported_days']==1096 and v['complete_week_count']==156 and not v['failures'];assert len(v['folds'][-1]['missing_raw_weeks'])==6;checks.append('actual fixed-plan/fold denominator')
print(json.dumps({'passed':checks,'failed':[]},sort_keys=True))
