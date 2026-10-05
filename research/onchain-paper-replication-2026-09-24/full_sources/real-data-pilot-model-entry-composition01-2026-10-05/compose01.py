from pathlib import Path
import hashlib,json,difflib,ast
D=Path(__file__).resolve().parent;F=D.parent;P=Path('tradingagents/research/onchain_replication')
policy=F/'real-data-pilot-full-size-policy01-2026-10-05';population=F/'real-data-pilot-population-binding01-2026-10-05'
base=policy/'candidate'/P/'real_pilot_import_caller.py';other=population/'real_pilot_import_caller.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=base.read_text()
s=replace(s,"    require(set(p) == fields | ({'resource_policy'} if full else set()), 'pilot plan fields differ')", "    resource_subset = 'population_scope' in p\n    require(not resource_subset or (full and p['population_scope'] == 'resource_pilot_subset'), 'explicit schema2 subset scope required')\n    require(set(p) == fields | ({'resource_policy'} if full else set()) | ({'population_scope'} if resource_subset else set()), 'pilot plan fields differ')")
s=replace(s,"    require(type(indices) is list and len(indices) == 16 and all(type(i) is int and i >= 0 for i in indices)\n            and indices == list(range(indices[0], indices[0]+16)), 'consecutive eligible batch16 required')", "    if resource_subset:\n        require(indices is None, 'resource indices must be derived by the registered worker')\n    else:\n        require(type(indices) is list and len(indices) == 16 and all(type(i) is int and i >= 0 for i in indices)\n                and indices == list(range(indices[0], indices[0]+16)), 'consecutive eligible batch16 required')")
s=replace(s,"    assembly = produce_registered_population(run,p['population_plan_input'])\n    examples,scaler = population_from_record(assembly['population'])\n    indices = p['indices']", "    resource_subset = p.get('population_scope') == 'resource_pilot_subset'\n    if resource_subset:\n        from .real_pilot_population import produce\n        examples,scaler,indices = produce(run,p['population_plan_input'],p)\n    else:\n        assembly = produce_registered_population(run,p['population_plan_input'])\n        examples,scaler = population_from_record(assembly['population'])\n        indices = p['indices']")
s=replace(s,"    require(assembly['provenance']['source_admission']['asset'] == 'ETH', 'real ETH source required')", "    if not resource_subset:\n        require(assembly['provenance']['source_admission']['asset'] == 'ETH', 'real ETH source required')")
# Keep population producer bytes unchanged. Its ten roles/output checks execute in
# its genuine worker; its immutable scope and price/calendar pins are not rebound.
raw=s.encode();ast.parse(raw);put(D/'candidate'/P/'real_pilot_import_caller.py',raw)
helper=(population/'real_pilot_population.py').read_bytes();put(D/'candidate'/P/'real_pilot_population.py',helper)
records=[]
for label,path in [('full-size-policy',base),('population-binding',other)]:
 old=path.read_bytes();put(D/'baseline'/(label+'.py'),old)
 a=old.decode().splitlines(True);b=s.splitlines(True)
 edits=[{'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':a[i:j],'new':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal']
 inv=b[:]
 for e in reversed(edits):assert inv[e['new_start']:e['new_end']]==e['new'];inv[e['new_start']:e['new_end']]=e['old']
 assert ''.join(inv).encode()==old
 put(D/(label+'.patch'),''.join(difflib.unified_diff(a,b,fromfile=label+'/real_pilot_import_caller.py',tofile='candidate/real_pilot_import_caller.py')).encode())
 records.append({'manifest_sha256':sha((policy/'MANIFEST01.json' if label=='full-size-policy' else population/'MANIFEST01.json').read_bytes()),'origin':str(path),'sha256':sha(old),'manifest':str(path.parents[4]/'MANIFEST01.json') if label=='full-size-policy' else str(population/'MANIFEST01.json'),'edits':edits})
native=[{'path':str(policy/'candidate'/P/n),'sha256':sha((policy/'candidate'/P/n).read_bytes())} for n in ['resources.py','job.py','resource_fixture.py']]
record={'schema_version':1,'caller_sha256':sha(raw),'baselines':records,'helper':{'path':str(population/'real_pilot_population.py'),'sha256':sha(helper),'byte_identical':True},'native_policy_reuse':native,'resource_envelope_chosen':False,'live_integration':False}
put(D/'COMPOSITION01.json',(json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps({'caller_sha256':sha(raw),'helper_sha256':sha(helper)}))
