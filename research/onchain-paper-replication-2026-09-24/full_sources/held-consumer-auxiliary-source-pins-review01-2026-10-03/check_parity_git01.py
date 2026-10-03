"""Independent inverse source and new Git-readback boundary checks only."""
import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;F=H.parent;C=F/'held-consumer-auxiliary-source-pins-preparation01-2026-10-03'
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-04/source')
def load(path,names,env):
 nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
for filename,rel,seam in [('generate_inputs01.py','fixture_tools/generate_inputs01.py','held_input_plan'),('build_release_draft01.py','proof_tools/build_release_draft01.py','held_metadata_draft')]:
 old=(C/(filename+'.baseline04.txt')).read_text();new=(C/filename).read_text();assert old==(S/rel).read_text()
 if filename.startswith('generate'):
  new=new[:new.index('AUXILIARY_ROLES=')]+new[new.index('def held_input_plan('):]
  new=new.replace(next(l for l in new.splitlines(True) if l.startswith('HELD_ROLES=')),next(l for l in old.splitlines(True) if l.startswith('HELD_ROLES=')),1)
 a=ast.parse(old);b=ast.parse(new);af=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name==seam);bf=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name==seam)
 lines=new.splitlines(True);lines[bf.lineno-1:bf.end_lineno]=old.splitlines(True)[af.lineno-1:af.end_lineno];restored=''.join(lines);assert restored==old and ast.dump(ast.parse(restored))==ast.dump(a)
 print('PASS exact inverse bytes/AST',filename,'and baseline actual Source04')
G={'Path':Path,'json':json,'hashlib':hashlib};load(C/'generate_inputs01.py',{'canonical','sha','require','HELD_ROLES','AUXILIARY_ROLES','_held_ref','held_auxiliary_metadata','held_input_plan','render_held_auxiliary_declaration'},G)
env={'G':G};load(C/'test_auxiliary01.py',{'role','fixture'},env)
fn=next(n for n in ast.parse((C/'build_release_draft01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='held_metadata_draft');start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='auxiliary' for t in n.targets));block=compile(ast.Module(body=fn.body[start:start+2],type_ignores=[]),str(C/'build_release_draft01.py'),'exec')
def run(corrupt=None):
 s,r=env['fixture']();files={p:('code '+p).encode() for p in s['source_files']};s['source_files']={p:G['sha'](b) for p,b in files.items()};s['package_files']={p:s['source_files'][p] for p in s['package_files']};s['source_origins']=[{'path':p,'sha256':G['sha'](b),'bytes':len(b)} for p,b in files.items()]
 r['auxiliary_sources']=env['role']('metadata/auxiliary.json',G['render_held_auxiliary_declaration'](r,s));exp=r['registration']['document']['experiments']['future-held-fixture'];exp['source_files']={**s['source_files'],**{r[n]['reference']['path']:r[n]['reference']['sha256'] for n in (*G['AUXILIARY_ROLES'],'auxiliary_sources')}}
 r['registration']=env['role']('metadata/registration.json',r['registration']['document'])
 for v in r.values():files[v['reference']['path']]=v['document'].encode() if isinstance(v['document'],str) else G['canonical'](v['document'])
 plan=G['held_input_plan'](r,s);calls=[]
 def read(root,ref):
  b=files[ref['path']];assert G['sha'](b)==ref['sha256'] and len(b)==ref['bytes'];return b
 def git(root,*args):
  calls.append(args)
  if args[0]=='merge-base':
   if corrupt=='ancestry':raise ValueError('actual branch test stand-in refusal')
   return b''
  commit,path=args[2].split(':',1);b=files[path]
  if args[1]=='-s':return str(len(b)+(1 if corrupt=='extent' and path=='metadata/allocation.json' else 0)).encode()
  if (corrupt=='code' and path.startswith('tradingagents/')) or (corrupt=='design_review' and commit=='2'*40 and path=='metadata/review.json') or (corrupt=='current_registration' and commit=='1'*40 and path=='metadata/registration.json'):return b'changed'
  return b
 ns={'plan':plan,'source_plan':s,'source':'1'*40,'design_source':'2'*40,'root':Path('/synthetic-only'),'roles':r,'builder':SimpleNamespace(_held_git=git,held_document=read),'generator':SimpleNamespace(AUXILIARY_ROLES=G['AUXILIARY_ROLES'],sha=G['sha']),'require':G['require']}
 exec(block,ns);assert ns['auxiliary']['committed_metadata_readback'] is True and ns['auxiliary']['budget_authority'] is None
 assert len(calls)==423;return ns
run();print('PASS synthetic consistent199code/current-design6metadata/423calls join; no authority')
for value in ['ancestry','extent','code','design_review','current_registration']:
 try:run(value)
 except ValueError:print('PASS refusal',value)
 else:raise AssertionError(value)
