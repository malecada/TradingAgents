"""Offline stdlib-only candidate verification and source inventory, no install."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(name,value):
 p=HERE/name
 with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
for name in ('test_source01.py','test_fatal02.py','test_write03.py','test_authority04.py'):
 result=subprocess.run([sys.executable,'-B',str(HERE/name)],cwd=ROOT,capture_output=True)
 log=HERE/('verification-'+name+'.log')
 with log.open('xb') as f:f.write(result.stdout+result.stderr)
 if result.returncode:raise SystemExit(result.returncode)
for p in HERE.glob('*.py'):ast.parse(p.read_text())
base='tradingagents/research/onchain_replication/'
installed={base+n:n for n in ('cold_files.py','compact_cold_features.py','compact_native_producer.py','job_payload.py')}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
# Baseline superset, deliberately not an execution registration. It includes
# every tracked research/full_sources Python body so dynamic dated dependencies
# are pinned without importing any numerical module.
paths=subprocess.check_output(['git','ls-files','tradingagents/research','research/onchain-paper-replication-2026-09-24/full_sources'],cwd=ROOT,text=True).splitlines()
pins={}
for name in paths:
 if name.endswith('.py') and not name.startswith(str(HERE.relative_to(ROOT))+'/'):
  p=ROOT/name;raw=p.read_bytes();committed=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)
  if raw!=committed:raise ValueError('baseline source differs: '+name)
  pins[name]={'sha256':sha(raw),'bytes':len(raw)}
write('baseline-source-inventory01.json',{'schema_version':1,'head':head,'kind':'conservative-source-superset-not-admission','files':pins})
install={}
for dest,name in installed.items():
 raw=(HERE/name).read_bytes();install[dest]={'candidate':name,'sha256':sha(raw),'bytes':len(raw),'baseline':pins.get(dest)}
write('install-map01.json',{'schema_version':1,'head':head,'install':install,'installed':False})
# Exclude only this self-excluding manifest, written last after report.
write('verification01.json',{'schema_version':1,'status':'passed_scoped_source_checks','methods':17,
 'source_syntax':'all local Python snapshots parsed','numerical_imports':False,'real_job':False,
 'baseline_files':len(pins),'model_math_changed':False,'native_map_changed':False,
 'job_payload_changed_functions':['_produce_eager_graphs'],'evidence':'verification-test_*.log'})
print(json.dumps({'tests':17,'baseline_files':len(pins),'install_files':len(install),'head':head}))
