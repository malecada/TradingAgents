import ast,hashlib,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;F=P.parent;A=F/'neural-cold-feature-handoff-comparison-parent-preparation01-2026-10-03';R=F/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'MANIFEST01.json')=='1cea5128a71024818328326a4742942d3a62259086f6a58b848888b7908110d3';m=json.loads((A/'MANIFEST01.json').read_bytes());assert len(m['files'])==9
for r in m['files']:assert sha(A/r['path'])==r['sha256'] and (A/r['path']).stat().st_size==r['bytes']
assert sum(r['bytes'] for r in m['files'])==37373
old=(A/'baseline-parent_wait05.py').read_text();new=(A/'comparison_parent05.py').read_text();d={'compact-cold-inputs-20261003-01':'compact-cold-comparison-20261003-01','"materialize"':'"compare"','this exact parent selects only materialization':'this exact parent selects only comparison'}
for x,y in d.items():assert old.count(x)==1;old=old.replace(x,y)
assert new==old
base=ast.parse((A/'baseline-parent_wait05.py').read_bytes());tree=ast.parse(new);changes=[]
def compare(a,b):
 if isinstance(a,ast.AST):
  assert type(a)==type(b)
  for k,v in ast.iter_fields(a):compare(v,getattr(b,k))
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):compare(x,y)
 elif a!=b:changes.append((a,b))
compare(base,tree);assert len(changes)==3
require=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='require');main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main');select=next(x for x in main.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and any(isinstance(t,ast.Constant) and t.value=='this exact parent selects only comparison' for t in x.value.args));code=compile(ast.Module(body=[require,select],type_ignores=[]),'exact-source-selection','exec')
for ident in ['compact-cold-inputs-20261003-01','compact-cold-comparison-20261003-01','other',None]:
 for phase in ['materialize','compare','other',None]:
  ns={'identity':ident,'request':{'phase':phase}}
  try:exec(code,ns);accepted=True
  except ValueError:accepted=False
  assert accepted==(ident=='compact-cold-comparison-20261003-01' and phase=='compare')
# Check actual recovery selection inputs and existing finite member metadata,
# without extracting/decoding the archive or invoking the recovery script.
p=F/'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03';pm=json.loads((p/'MANIFEST02.json').read_bytes());assert len(pm['files'])==25
for r in pm['files']:assert sha(p/r['path'])==r['sha256']
assert sha(p/'collector01.py')=='d3ab84766f8a0e42d1247f5620b9a331fc1975d38e6447ee192bb2b1324d0b69'
closure=F/'neural-cold-feature-handoff-materialization-closure-review01-2026-10-03'
for n in ['REVIEW_CLOSURE01.md','MANIFEST01.json','readback01.json','REQUEST_REVIEW01.json','PROCESS_NATIVE_READBACK01.json','check01.py','check01.log']:assert (closure/n).is_file()
ret=json.loads((R/'OUTCOME_RETENTION01.json').read_bytes());assert ret['member_count']==len(ret['members'])==1023;assert len({x['path'] for x in ret['members']})==1023;assert ret['files']==746 and ret['directories']==277 and ret['logical_bytes']==6291908;assert (R/'materialization-outcome01.tar.gz').stat().st_size==ret['archive_bytes']==2563986
assert all(r['bytes']<=4194304 and r['kind'] in ['file','directory'] for r in ret['members'])
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'parent_manifest_sha256':sha(A/'MANIFEST01.json'),'parent_sha256':sha(A/'comparison_parent05.py'),'nine_manifest_members_verified':True,'exact_three_literal_byte_delta':True,'whole_AST_changes':changes,'selection_matrix_cases':16,'only_comparison_selected':True,'collector_manifest_members_verified':25,'outcome_helper_sha256':sha(R/'recover_outcome01.py'),'existing_archive_bytes':ret['archive_bytes'],'metadata_member_count':1023,'no_recovery_execution_or_network_or_numerics':True},indent=2))
