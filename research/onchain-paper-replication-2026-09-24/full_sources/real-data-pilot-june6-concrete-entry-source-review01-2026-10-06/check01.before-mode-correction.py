from pathlib import Path
import ast,copy,hashlib,importlib.util,inspect,json,stat,tempfile
from unittest.mock import patch
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent
A=F/'real-data-pilot-june6-concrete-entry-preparation02-2026-10-06'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):
    assert p.stat().st_size<4*1024**2
    return json.loads(p.read_bytes())
manifest=A/'MANIFEST01.json';assert sha(manifest.read_bytes())=='51d3b47f05087c87127b76206001f8fad8afd3739f1b053c7af1ce3f67fb867e'
for name,row in read(manifest)['files'].items():
    p=A/name;b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==0o444
sp=importlib.util.spec_from_file_location('review_boundary',A/'boundary01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
D=F/'real-data-pilot-sixth-graph-input-preparation01-2026-10-06/draft01'
p=read(D/'STORAGE_PROJECTION_DRAFT01.json');scope=m.storage_scopes(p)
assert scope['physical_root_growth_bytes']==7155620336
assert scope['named_sources_growth_bytes']==6744020747
assert scope['physical_root_growth_bytes']-scope['named_sources_growth_bytes']==411599589
assert scope['physical_startup_free_bytes']==17893038576
assert scope['named_rollback_journal_allowance_bytes']==3099885508
results=[]
def refuse(label,call):
    try:call()
    except ValueError as e:results.append({'case':label,'error':str(e)})
    else:raise AssertionError(label)
for field,value in [('density_projected_ledger_bytes',True),('largest_projected_parquet_logical_bytes',0),('prospective_growth_estimate_bytes',6744020747),('prospective_startup_free_bytes',17893038575)]:
    bad=copy.deepcopy(p);bad[field]=value;refuse(field,lambda:m.storage_scopes(bad))
draft=read(A/'BOUNDARY_CURRENT_TERMINAL_DRAFT01.json')
assert [k for k,v in draft['dependencies'].items() if v is None]==['continuation_outcome_review','continuation_recovery_review','post_continuation_accounting']
with patch.object(m,'read',side_effect=AssertionError('cold refusal performed dependency IO')):
    refuse('missing independent proof before dependency IO',lambda:m.check(draft))
    bad=copy.deepcopy(draft);bad['identity']='other';refuse('wrong identity',lambda:m.check(bad))
    bad=copy.deepcopy(draft);bad['parent']='old';refuse('parent transfer',lambda:m.check(bad))
# Pure refusal witness supplies only metadata needed to reach failed terminal; no success authority.
bad=copy.deepcopy(draft)
for k in m.FUTURE:bad['dependencies'][k]={'path':k,'sha256':'a'*64}
bad['dependencies']['continuation_claim']['path']='research_runs/'+m.CONT+'/claim.json'
bad['dependencies']['continuation_terminal']['path']='research_runs/'+m.CONT+'/complete.json'
docs={k:{} for k in bad['dependencies']};docs['continuation_claim']={'experiment_id':m.CONT,'source':'s'};docs['continuation_terminal']={'experiment_id':m.CONT,'source':'s','claim_sha256':'a'*64,'status':'failed'}
with patch.object(m,'read',side_effect=lambda ref:docs[next(k for k,v in bad['dependencies'].items() if v==ref)]):refuse('failed terminal',lambda:m.check(bad))
# Independent tree transform: remove exactly declared two new scope blocks from check only.
text=(A/'preflight01.py').read_text();tree=ast.parse(text);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check')
nodes=fn.body;starts=[i for i,n in enumerate(nodes) if isinstance(n,ast.ImportFrom) and n.module=='boundary01'];assert len(starts)==1
i=starts[0];assert len(nodes[i:i+4])==4 and isinstance(nodes[i+3],ast.If);del nodes[i:i+4]
i=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='limits');assert isinstance(nodes[i+1],ast.If);del nodes[i:i+2]
restored=ast.unparse(fn).replace('admission.effective_attempt_budget != 72','admission.effective_attempt_budget != 71').replace("'effective_attempt_budget': 72","'effective_attempt_budget': 71").replace('preceding_continuation_boundary','failed_predecessor_retained').replace('fresh storage policy must bind actual continuation closure, preserved failure and separate Data retention','fresh storage policy must explicitly retain failed originals and recoveries; no retirement credit')
base=F/'real-data-pilot-sixth-graph-failed-predecessor-entry01-2026-10-06/preflight01.py';oldfn=next(n for n in ast.parse(base.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='check');assert ast.dump(ast.parse(restored).body[0])==ast.dump(oldfn)
assert (A/'launch01.py').read_bytes()==(F/'real-data-pilot-sixth-graph-entry-preparation01-2026-10-06/launch01.py').read_bytes()
basis=m.temporary_file_basis();tf=inspect.getsource(tempfile.TemporaryFile);assert '_os.O_TMPFILE' in tf and tf.index('_os.unlink(name)')<tf.index('return fd',tf.index('_os.unlink(name)'))
source=R/'tradingagents/research/onchain_replication/eth_source.py';tree=ast.parse(source.read_text());project=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='projected_parquet');w=next(n for n in project.body if isinstance(n,ast.With));assert ast.unparse(w.items[0].context_expr)=='tempfile.TemporaryFile(dir=scratch)' and ast.unparse(w.body[0])=='file.truncate(size)'
pins=read(A/'CHECK_SCOPE01.json')['source_pins']
for path,expected in pins.items():assert sha((R/path).read_bytes())==expected
for key,ref in draft['dependencies'].items():
    if ref is not None: assert sha((R/ref['path']).read_bytes())==ref['sha256']
actual=m.read(draft['dependencies']['continuation_root']);assert actual['actual_root_tool_exit_code']==actual['original_outer_exit_code']==0 and actual['source_commit']==m.read(draft['dependencies']['continuation_claim'])['source']
for name in ('prepare01.py','preflight01.py','boundary01.py','launch01.py'):compile((A/name).read_bytes(),name,'exec')
result={'decision':'pass-source-only','manifest_sha256':sha(manifest.read_bytes()),'sealed_members_verified':len(read(manifest)['files']),'scope':scope,'stdlib':basis,'refusals':results,'preflight_check_AST_inverse':True,'launcher_byte_identical':True,'actual_terminal_draft_nonnull_pins_verified':True,'source_pins':pins,'no_preparer_preflight_admission_launch':True,'payload_reads':0,'live_baseline_sampled':False,'capacity_proved':False}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
