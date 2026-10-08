import ast,copy,hashlib,importlib,json,pathlib,sys,tempfile,types
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent;F=HERE.parent
C=F/'real-data-pilot-checkpoint-throughput-composition01-2026-10-08'
S=F/'real-data-pilot-sharded-checkpoint-candidate01-2026-10-08'
A=F/'real-data-pilot-advance-validation-correction01-2026-10-08'
P=F/'real-data-pilot-matching-capacity-override01-2026-10-08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((C/'COMPOSITION01.json').read_text())
assert sha(P/'MANIFEST02.json')==record['capacity_manifest_sha256']
for n,h in record['sources'].items():assert sha(C/n)==h
for n,h in json.loads((P/'MANIFEST02.json').read_text())['files'].items():assert sha(P/n)==h
for n in ('checkpoint_chunks.py','matching_hardening.py','matching_pair.py','restart_retention.py','stage_retention.py'):assert (C/n).read_bytes()==(S/n).read_bytes()
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
for name,functions in [('matching_annealing.py',('advance','_advance_checked')),('matching_checkpoint.py',('advance',))]:
 for fn in functions:assert funcs(C/name)[fn]==funcs(A/name)[fn]
for name in ('matching_annealing.py','matching_checkpoint.py'):
 old,new=funcs(S/name),funcs(C/name)
 for fn in old:
  if fn!='advance':assert old[fn]==new[fn]
# Real existing ArchivePairLog with disposable local synthetic transport; candidate
# package shares unchanged typed graph and archive class identities explicitly.
from tests.research.onchain_replication import test_compact_matcher as tiny
from tests.research.onchain_replication import test_restart_retention_integration as retained
pkg=types.ModuleType('joint_candidate');pkg.__path__=[str(C),str(pathlib.Path.cwd()/'tradingagents/research/onchain_replication')];sys.modules[pkg.__name__]=pkg
for n in ('contracts','compact_pair_log','archive_pair_writer','score_batches','provenance','matching_identity','cache'):
 sys.modules['joint_candidate.'+n]=importlib.import_module('tradingagents.research.onchain_replication.'+n)
matcher=importlib.import_module('joint_candidate.compact_matcher');policy=matcher.compact_policy
store=importlib.import_module('joint_candidate.restart_retention')
checks=[]
def check(name,condition):assert condition,name;checks.append(name)
def refuse(name,fn):
 try:fn()
 except ValueError:checks.append(name);return
 raise AssertionError(name+' accepted')
base=tiny.POLICY;original=tiny.config()|{'max_pair_entries':1}
layout={'format':'sharded-npy-v1','chunk_entries':2}
joint=base|{'checkpoint_layout':layout,'max_pair_entries_override':4}
for p in (base,base|{'checkpoint_layout':layout},base|{'max_pair_entries_override':4},joint):policy.pair_policy(p)
check('all four optional field combinations',True)
for x in (0,-1,True,1.5,2**63,'4',{'max_pair_entries':4}):refuse('invalid override '+repr(x),lambda x=x:policy.effective_matching(original,joint|{'max_pair_entries_override':x}))
refuse('decrease refusal',lambda:policy.effective_matching(original|{'max_pair_entries':5},joint))
for key in ('alpha','beta0','solver'):refuse('semantic field refusal '+key,lambda key=key:policy.effective_matching(original,joint|{key:2}))
check('original config retained',policy.effective_matching(original,joint)==original|{'max_pair_entries':4} and original['max_pair_entries']==1)
components=matcher._components(layout,joint)
check('chunks and capacity source pinned',any(k.startswith('checkpoint_chunks.py:') for k in components) and any(k.startswith('compact_policy.py:') for k in components))

def fixture(root,p,c):
 with patch.object(retained,'matcher_module',matcher),patch.object(tiny,'POLICY',p),patch.object(tiny,'config',return_value=c):
  return retained.fixture(root,progress=True,schedule_override={'operations_per_call':1,'calls_per_checkpoint':4,'max_checkpoints':10})
for which in ('joint','default'):
 with tempfile.TemporaryDirectory(prefix='joint-review-') as d:
  root=pathlib.Path(d);p=joint if which=='joint' else base;c=original if which=='joint' else tiny.config()
  m,log,a,b,c,purpose,transport=fixture(root,p,c)
  try:
   if which=='joint':
    check('scope retains original config',log.start['scope']['config']==matcher.cache_key(c))
    check('controller config effective',m.retention.claim['config']==m.config and m.retention.claim['pair_policy']==p)
    refuse('original cannot allocate larger pair',lambda:matcher.engine.create(a,b,c,**{k:p[k] for k in matcher.pair.ENGINE_FIELDS}))
   result=m(purpose,a,b)
   expected=retained.match_reference(a,b,m.config)
   check(which+' complete score bitwise',result['score'].hex()==expected.score.hex())
   check(which+' actual archived progress',log.state['progress_events']>0 and log.state['completed_pairs']==1)
   reference=m.retention.finish_stage();terminal=log.finish()
   check(which+' terminal and stage seal',bool(reference and terminal))
   path=next((root/'checkpoints/stores').iterdir())
   terminal_body=json.loads((path/'terminal.json').read_bytes())
   out=store.verify(path,expected_claim=terminal_body['claim_sha256'],expected_terminal=sha(path/'terminal.json'))
   check(which+' actual store retirement replay verification',out['generations']>0 and len(out['retired'])==out['generations'] and list(out['replays'])==[0])
   replay=path/'replay-00000000000000000000'
   check(which+' replay layout',bool(list(replay.rglob('M-00000000.npy'))) if which=='joint' else bool(list(replay.rglob('M.npy'))))
  finally:log.close()
for which in ('original','effective','policy','layout'):
 with tempfile.TemporaryDirectory(prefix='joint-mutation-') as d:
  m,log,*_=fixture(pathlib.Path(d),joint,original)
  try:
   if which=='original':m.original_config['alpha']+=1
   elif which=='effective':m.config['alpha']+=1
   elif which=='policy':m.policy['max_pair_entries_override']+=1
   else:m.checkpoint_layout['chunk_entries']+=1
   refuse(which+' late mutation',m._check)
  finally:log.close()
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'scope':'synthetic actual ArchivePairLog/Controller/Store; no genuine scientific Owner or real inputs'},indent=2))
