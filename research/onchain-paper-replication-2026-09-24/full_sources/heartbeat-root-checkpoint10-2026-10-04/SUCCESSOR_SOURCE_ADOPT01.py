from pathlib import Path
import ast,hashlib,json,subprocess
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';a=f/'financial-wrapper-continuation-successor-source01-2026-10-05';d=f/'financial-wrapper-continuation-successor-preparation02-2026-10-05';r=f/'financial-wrapper-continuation-successor-review01-2026-10-05';cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');p=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
 with path.open('xb') as w:w.write(b)
assert sha((a/'MANIFEST01.json').read_bytes())=='36689eae6e875be08c97a6efe7438b8dfa4bb166f8dd8347ebf27c3c0e2a3b16'
assert sha((r/'SOURCE_REVIEW_PROOF01.json').read_bytes())=='cff01105b5b340359a051b721e85717e6e1e3888a2f612782ee2f0829d702cfd'
assert subprocess.run(['git','status','--short','--untracked-files=no'],cwd=cap,capture_output=True,text=True,check=True).stdout==''
oldhead=subprocess.run(['git','rev-parse','HEAD'],cwd=cap,capture_output=True,text=True,check=True).stdout.strip();assert oldhead=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
edge=json.loads((d/'successor.json').read_bytes());prefix='tradingagents/research/onchain_replication/';old=json.loads((cap/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes())['target']['installed'];changes=[]
for name in ('operational_source_compatibility.py','financial_wrapper_fixture.py'):
 dest=cap/(prefix+name);before=dest.read_bytes();body=(a/name).read_bytes();assert sha(before)==old[prefix+name] and sha(body)==edge['installed'][prefix+name];ast.parse(body);dest.write_bytes(body);changes.append({'path':prefix+name,'before':sha(before),'after':sha(body)})
inputs=cap/'fixture_inputs/financial_wrapper_continuation_successor01';assert not inputs.exists();inputs.mkdir(mode=0o700)
for name in ('successor.json','source_closure.json','continue-plan.json','refusal.json'):put(inputs/name,(d/name).read_bytes())
put(inputs/'successor-review.json',(r/'SOURCE_REVIEW_PROOF01.json').read_bytes())
put(p/'preclaim01.py',(a/'preclaim01.py').read_bytes())
draft=(p/'parent01.py').read_bytes();put(c/'SUCCESSOR_PARENT_SOURCE_UNBOUND01.py',draft);text=draft.decode();assert text.count('SUCCESSOR_FIXTURE_SHA256=None')==1;text=text.replace('SUCCESSOR_FIXTURE_SHA256=None',"SUCCESSOR_FIXTURE_SHA256='"+edge['installed'][prefix+'financial_wrapper_fixture.py']+"'");ast.parse(text);(p/'parent01.py').write_text(text)
record={'schema_version':1,'status':'accepted-source-adopted-no-release','prior_cap_head':oldhead,'changed_installed_bodies':changes,'installed_scientific_map_count':195,'other_installed_paths_changed':False,'new_input_files':{x.name:sha(x.read_bytes()) for x in sorted(inputs.iterdir())},'external_preclaim_sha256':sha((p/'preclaim01.py').read_bytes()),'caller_unbound_sha256':sha((p/'parent01.py').read_bytes()),'source_review_sha256':sha((r/'SOURCE_REVIEW_PROOF01.json').read_bytes()),'pending':'actual successor-policy recovery, concrete committed gate/current source binding, full recovery and exact final release','numerical_import':False,'claim':False}
put(c/'SUCCESSOR_SOURCE_ADOPTION01.json',enc(record));print(json.dumps({'adopted_installed_bodies':2,'new_input_files':5,'external_preclaim':True,'claim':False}))
