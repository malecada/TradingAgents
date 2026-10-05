"""Probe exact pinned original Reader with real opaque bodies. No public validator/entry.
Run only with an explicit inventoried JSON and fresh output name in this preparation.
A budget refusal is retained as an observed limitation, never a successful preclaim.
"""
from pathlib import Path
import json,hashlib,importlib.util,argparse,time,sys
H=Path(__file__).resolve().parent
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01/preclaim01.py')
PIN='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(P.read_bytes())==PIN
spec=importlib.util.spec_from_file_location('_unchanged_continuation_reader',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=argparse.ArgumentParser();a.add_argument('--inventory',type=Path,required=True);a.add_argument('--out',required=True);args=a.parse_args();assert args.inventory.resolve().parent==H and Path(args.out).name==args.out and not (H/args.out).exists()
body=args.inventory.read_bytes();v=json.loads(body);rows=v['rows'];assert len(rows)<=512 and len({x['path'] for x in rows})==len(rows) and all(type(x['bytes'])is int and 0<=x['bytes']<=m.FILE for x in rows)
r=m.Reader();first=None;failure=None;phase='initial-read';begun=time.monotonic()
try:
 for x in rows:
  b=r.read(Path(x['path']));assert len(b)==x['bytes'] and sha(b)==x['sha256']
 first=r.total;phase='finish';r.finish();phase='complete'
except m.Unavailable as error:
 failure={'type':type(error).__name__,'reason':str(error),'phase':phase}
 if str(error) not in ('preclaim total byte bound','preclaim total actual byte bound'):raise
assert not any(n in sys.modules for n in ('numpy','torch','scipy','pandas'))
out={'schema_version':1,'status':'MEASURED_ORIGINAL_READER_BUDGET_REFUSAL' if failure else 'MEASURED_BYTE_SET_ONLY_NOT_ADMISSION','reader_sha256':PIN,'inventory_sha256':sha(body),'unique_paths_loaded':len(r.cache),'expected_paths':len(rows),'first_pass_bytes':first,'observed_charged_bytes_before_return_or_refusal':r.total,'expected_read_plus_finish':2*sum(x['bytes'] for x in rows),'reader_limit':m.TOTAL,'failure':failure,'seconds':time.monotonic()-begun,'checkpoint_bytes_read_as_opaque':True,'checkpoint_deserialized':False,'project_public_validator_executed':False,'genuine_admission_created':False,'numerical_authority':False}
with (H/args.out).open('x') as f:json.dump(out,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps(out))
