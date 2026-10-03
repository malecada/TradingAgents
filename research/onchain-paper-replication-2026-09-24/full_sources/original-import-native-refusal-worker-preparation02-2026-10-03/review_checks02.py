"""Independent stdlib metadata/actual-tail checks, never an authority or job."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,types
P=Path(__file__).resolve().parent;R=P.parents[3];OLD=P.parent/'original-import-native-refusal-worker-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
m=read(P/'MANIFEST02.json')
for row in m['files']+m['dependencies']:
 b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
inv=read(P/'source_inventory02.json');old=read(OLD/'source_inventory01.json');rows={r['target']:r for r in inv['source_inventory']};before={r['target']:r for r in old['source_inventory']}
assert len(rows)==169 and sum(n.startswith('tradingagents/') for n in rows)==144
for row in rows.values():
 b=(R/row['origin']).read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes']
assert [n for n in rows if rows[n]!=before[n]]==['fixture_tools/refusal_outer01.py']
for n in ['resource_refusal.py','refusal_native01.py','refusal_preclaim01.py','refusal_oracle_evidence01.py','templates01.py']:assert (P/n).read_bytes()==(OLD/n).read_bytes()
assert read(P/'PROTOCOL02.json')==read(OLD/'PROTOCOL01.json')
proto=read(P/'PROTOCOL02.json');assert (len(proto['case_order']),len(proto['preclaim']),proto['max_claims'],proto['max_owners'],proto['max_journals'],proto['max_oracle_pairs'],proto['max_scored_pairs'])==(27,4,23,17,19,1088,129)
assert len(set(proto['case_order']))==27 and 17*64==1088
release=read(P/'qualified-release-draft02.json');assert len(release['cases'])==27 and release['source_files']=={n:r['sha256'] for n,r in rows.items()}
assert release['capsule_commit']=='a'*40 and release['capsule_root']=='/qualified-unregistered-synthetic'
# Whole AST inverse move proves no other outer behavior changed.
source=P/'refusal_outer01.py';tree=ast.parse(source.read_text());prior=ast.parse((OLD/'refusal_outer01.py').read_text())
def fun(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
run=fun(tree,'run');guard=next(n for n in run.body if isinstance(n,ast.Try) and any(isinstance(x,ast.For) and 'signal_handlers.items' in ast.unparse(x) for x in n.finalbody))
post=next(n for n in guard.finalbody if isinstance(n,ast.Try) and 'publish_post_tail(root, watch, save)' in ast.unparse(n));marker=guard.finalbody[-1];assert isinstance(marker,ast.If)
post.handlers[0].body.append(marker.body[0]);guard.finalbody.pop()
assert ast.dump(tree)==ast.dump(prior)
# Actual selected owned_io class, no package import.
row=rows['tradingagents/research/onchain_replication/owned_io.py'];spec=importlib.util.spec_from_file_location('review_owned_io',R/row['origin']);owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
def exercise(primary=None,post_error=None,restores=(None,None),marker_error=None):
 t=ast.parse(source.read_text());run=fun(t,'run');g=next(n for n in run.body if isinstance(n,ast.Try) and any(isinstance(x,ast.For) and 'signal_handlers.items' in ast.unparse(x) for x in n.finalbody));start=next(i for i,n in enumerate(g.finalbody) if isinstance(n,ast.Try) and 'publish_post_tail(root, watch, save)' in ast.unparse(n));tail=g.finalbody[start:]
 env={};exec(compile(ast.Module(body=[fun(t,'select')],type_ignores=[]),'actual reducer','exec'),env)
 receipts={'terminal.json':{'status':'passed'}};events=[];errors=iter(restores)
 def retain(e):env['primary']=env['select'](env['primary'],e,owned.CleanupFailure)
 def publish(*args):
  events.append('post')
  if post_error is not None:raise post_error
 def restore(*args):
  events.append('restore');e=next(errors)
  if e is not None:raise e
 def save(name,v):
  events.append('marker');assert name=='post-terminal-failure.json' and name not in receipts
  if marker_error is not None:raise marker_error
  receipts[name]=v
 env.update(primary=primary,publish_post_tail=publish,root=None,watch=None,save=save,result={},authenticate_post_tail=lambda *args:{},identity='synthetic-unclaimed',entry={'job_resources':{}},source='a'*40,retain=retain,signal_handlers={2:None,15:None},signal=types.SimpleNamespace(signal=restore))
 exec(compile(ast.Module(body=tail,type_ignores=[]),'actual tail','exec'),env)
 assert receipts['terminal.json']=={'status':'passed'} and events[:3]==['post','restore','restore']
 if env['primary'] is not None:assert events.count('marker')==1
 else:assert events.count('marker')==0
 return env['primary'],receipts
checks=0
ordinary1=OSError('restore1');ordinary2=ValueError('restore2');fatal1=MemoryError('first');fatal2=KeyboardInterrupt('second');uncertain=owned.CleanupFailure('uncertain')
for kwargs,expected in [({},None),({'restores':(ordinary1,ordinary2)},ordinary1),({'primary':fatal1,'restores':(ordinary1,fatal2)},fatal1),({'post_error':ordinary1,'restores':(fatal2,fatal1)},fatal2),({'primary':uncertain,'restores':(fatal1,fatal2)},fatal1),({'restores':(ordinary1,ordinary2),'marker_error':fatal1},fatal1),({'primary':fatal1,'restores':(ordinary1,fatal2),'marker_error':MemoryError('marker')},fatal1),({'restores':(ordinary1,None),'marker_error':uncertain},uncertain),({'post_error':ordinary1},ordinary1)]:
 actual,receipts=exercise(**kwargs);assert actual is expected
 if expected is not None and not kwargs.get('marker_error'):assert receipts['post-terminal-failure.json']['error_type']==type(expected).__name__
 checks+=1
# Actual parser early-refusal branch exercised with synthetic existence only;
# no durable caller/native result is invented.
row=rows['fixture_tools/raw_receipts01.py'];parser=ast.parse((R/row['origin']).read_text());f=fun(parser,'authenticate_post_tail');assert 'post-terminal-failure.json' in ast.unparse(f)
assert not {'numpy','torch','scipy','tradingagents'}&set(sys.modules)
print(json.dumps({'manifest_sha256':sha((P/'MANIFEST02.json').read_bytes()),'manifest_bodies':len(m['files']),'dependencies':len(m['dependencies']),'source_count':169,'package_count':144,'unchanged_targets':168,'only_changed_target':'fixture_tools/refusal_outer01.py','inverse_tail_move_full_AST_equal':True,'independent_actual_tail_combinations':checks,'genuine_selected_cleanup_class':True,'prospective_variants':27,'classes':16,'preclaim':4,'max_claims':23,'max_owners':17,'max_journals':19,'prospective_identity_comparisons':1088,'scored_pair_maximum':129,'actual_attempts':0,'numerical_imports':False},indent=2))
