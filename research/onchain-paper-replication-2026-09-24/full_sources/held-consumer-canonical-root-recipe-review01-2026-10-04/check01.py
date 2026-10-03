"""Independent fixed source/opaque-body joins and bounded pure recipe controls."""
import ast,copy,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'held-consumer-canonical-root-recipe01-2026-10-04';G=C/'generated01'
sys.path.insert(0,str(C))
import prepare01 as P
import rebind01 as R
checks=[];git_calls=[];observations=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2;return p.read_bytes()
def git(args,data=None):
 env=os.environ.copy();env.update(GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1')
 r=subprocess.run(['git','-c','protocol.allow=never','-C',str(P.CAP),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15)
 assert r.returncode==0 and len(r.stdout)<=4*1024**2 and len(r.stderr)<=65536
 git_calls.append({'args':args,'stdout_bytes':len(r.stdout),'stdout_sha256':sha(r.stdout)})
 return r.stdout
pins={'prepare01.py':'631870b67284e1dbc9e9ce07c63c2b35604f3b9a6629a2b1a9f9c39550ce7f6c','rebind01.py':'791a2c36f3c89c2e3d42870c3554294aa3fa23b0b46d12d47228418d2dec3cda','DRAFT_CASES02.json':'76d6e332e7cd30c44022a65501340525090efc8089fa316b636393e2d5f52324','MANIFEST01.json':'05393053abb828e3980b01a6911d6e602ee488a34f4d988c90f1a43fab27fd35'}
for name,pin in pins.items():ok('candidate exact '+name,sha(read(C/name))==pin)
rows=json.loads(read(C/'MANIFEST01.json'))['entries']
ok('complete618/518',len(rows)==618 and sum(r['type']=='file' for r in rows)==518)
ok('no duplicate or omitted paths',len({r['path'] for r in rows})==len(rows) and {p.relative_to(C).as_posix() for p in C.rglob('*')}=={r['path'] for r in rows}|{'MANIFEST01.json'})
for r in rows:
 p=C/r['path'];s=p.lstat();ok('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['type']=='file':ok('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(read(p))==r['sha256'])
 else:ok('directory '+r['path'],r['type']=='directory' and stat.S_ISDIR(s.st_mode))
ok('actual old HEAD immutable',git(['rev-parse','HEAD']).decode().strip()==P.HEAD)
actualtree={}
for row in git(['ls-tree','-rz',P.HEAD]).split(b'\0'):
 if row:
  fields,name=row.split(b'\t');mode,kind,oid=fields.decode().split();actualtree[name.decode()]={'mode':mode,'kind':kind,'oid':oid}
inventory=json.loads(read(G/'SOURCE_MAP01.json'));entries=inventory['entries'];before={r['path']:r['baseline_sha256'] for r in entries};after={r['path']:r['candidate_sha256'] for r in entries}
ok('199/148 distinct source closure',len(entries)==len(before)==199 and sum(p.startswith('tradingagents/') for p in before)==148)
ok('198 unchanged one accepted replacement',[p for p in before if before[p]!=after[p]]==[P.CHANGE] and before[P.CHANGE]==P.OLD and after[P.CHANGE]==P.NEW)
for r in entries:
 p=r['path'];base=read(P.CAP/p);a=read(G/'baseline'/p);b=read(G/'candidate'/p);obj=actualtree[p]
 ok('actual baseline bytes '+p,base==a and sha(base)==r['baseline_sha256'] and len(base)==r['baseline_bytes'])
 ok('candidate bytes '+p,sha(b)==r['candidate_sha256'] and len(b)==r['candidate_bytes'])
 ok('actual blob OID '+p,obj['kind']=='blob' and obj['oid']==r['baseline_git_oid']==hashlib.sha1(b'blob '+str(len(base)).encode()+b'\0'+base).hexdigest())
 ok('candidate calculated blob OID '+p,r['candidate_git_blob_oid']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest())
 ok('all physical and git modes '+p,obj['mode']==r['git_mode'] and stat.S_IMODE((P.CAP/p).stat().st_mode)==r['physical_mode']==stat.S_IMODE((G/'baseline'/p).stat().st_mode)==stat.S_IMODE((G/'candidate'/p).stat().st_mode) and (int(obj['mode'],8)&0o111)==(r['physical_mode']&0o111))
gate=json.loads(read(P.CAP/'held-fixture-registration01.json'));ok('historical gate exact',read(P.CAP/'held-fixture-registration01.json')==read(G/'GATE_HISTORICAL.json'))
aux=json.loads(read(P.CAP/'held-auxiliary-success01.json'));excluded={r['reference']['path'] for r in aux['entries']}|{'held-auxiliary-success01.json'}
ok('actual implementation separation',before=={p:v for p,v in gate['experiments'][P.CASES['success']]['source_files'].items() if p not in excluded})
# The exact independent review bodies are authenticated, not their conclusions re-created.
for rel,pin in json.loads(read(C/'REVIEW_PINS01.json')).items():ok('independent accepted evidence '+rel,sha(read(C.parent/rel))==pin)
for origin,r in json.loads(read(G/'ORIGINS01.json')).items():ok('actual preserved review/source origin '+origin,sha(read(Path(origin)))==r['sha256']==sha(read(G/r['copy'])) and len(read(G/r['copy']))==r['bytes'])
fatal=C.parent/'held-consumer-canonical-fatal-supplement01-2026-10-03';canonical=C.parent/'held-consumer-canonical-successor-preparation01-2026-10-03'
new=read(G/'candidate'/P.CHANGE);canon=read(canonical/'original_dictionary.py');old=read(G/'baseline'/P.CHANGE);inv=json.loads(read(fatal/'INVERSE01.json'))
ok('accepted full e05 exact',new==read(fatal/'original_dictionary.py'))
ok('fatal full-byte inverse',new.count(inv['new_text'].encode())==1 and new.replace(inv['new_text'].encode(),inv['old_text'].encode())==canon)
def slice(raw):
 t=ast.parse(raw);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
 start=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='indices')
 end=next(i for i,n in enumerate(f.body) if i>start and isinstance(n,ast.Expr) and 'repeated representative' in ast.unparse(n));return t,f,start,end
at,af,a,z=slice(old);bt,bf,b,w=slice(canon);lines=canon.decode().splitlines(keepends=True);lines[bf.body[b].lineno-1:bf.body[w].end_lineno]=old.decode().splitlines(keepends=True)[af.body[a].lineno-1:af.body[z].end_lineno]
ok('canonical full-byte inverse',''.join(lines).encode()==old)
bf.body[b:w+1]=copy.deepcopy(af.body[a:z+1]);ok('canonical all-other AST inverse',ast.dump(at)==ast.dump(bt))
provenance=json.loads(read(G/'ORIGINAL_PROVENANCE01.json'));claim=json.loads(read(P.CAP/'fixture_inputs/original/08-claim.json'));objects=provenance['source_objects']
ok('original C6 claim26 source objects',claim['source']==provenance['original_source']=='c6b568d4b1c177ab94ac37fbad462c2decc721c0' and len(objects)==26 and {r['path']:r['sha256'] for r in objects}==claim['experiment']['source_files'])
request=''.join(claim['source']+':'+r['path']+'\n' for r in objects).encode();batch=git(['cat-file','--batch'],request);offset=0
for r in objects:
 end=batch.index(b'\n',offset);oid,kind,size=batch[offset:end].decode().split();n=int(size);body=batch[end+1:end+1+n]
 ok('actual C6 object '+r['path'],kind=='blob' and oid==r['git_oid'] and n==r['bytes'] and sha(body)==r['sha256'] and body==read(G/'original-c6-source'/r['path']) and batch[end+1+n:end+2+n]==b'\n');offset=end+2+n
ok('exact C6 batch framing',offset==len(batch))
frozen=json.loads(read(C/'DRAFT_CASES02.json'));allpaths={}
fresh=str(H/'uncreated-opaque-capsule'/'source')
for case,identity in P.CASES.items():
 exp=gate['experiments'][identity];draft,bodies=R.rebind(case);other,bodies2=R.rebind(case)
 ok(case+' deterministic exact frozen null draft',draft==other==frozen[case] and bodies==bodies2)
 ok(case+' exact roles/inputs/outputs',len(draft['roles'])==15 and len(draft['experiment']['inputs'])==33 and draft['experiment']['outputs']==exp['outputs'] and len(exp['outputs'])==6)
 ok(case+' candidate199 no inherited204pins',draft['experiment']['source_files']==after)
 for field in ('fresh_identity','source_commit','design_source','registration_commit','capsule_root','caller','independent_review','full_recovery','dependent_success_evidence','cumulative_allocation'):ok(case+' null '+field,draft[field] is None)
 ok(case+' authority not reused',all(draft['roles'][r] is None for r in ('registration','budget_extension','budget_review','charter','budget_allocation','auxiliary_sources','case_contract')) and draft['case_contract']['experiment_id'] is None)
 for role,ref in exp['inputs'].items():
  raw=read(P.CAP/ref['path']);ok(case+' opaque input '+role,raw==read(G/'input-baseline'/ref['path']) and sha(raw)==ref['sha256']);allpaths[ref['path']]=sha(raw)
  if role not in ('execution_job','execution_workspace'):ok(case+' unchanged input reference '+role,draft['experiment']['inputs'][role]==ref)
  ok(case+' no old held identity in input '+role,not any(s.encode() in raw for s in P.CASES.values()))
 bound,moved=R.rebind(case,fresh);bound2,moved2=R.rebind(case,fresh);ok(case+' fresh deterministic transform',bound==bound2 and moved==moved2 and not Path(fresh).exists())
 jobpath=exp['inputs']['execution_job']['path'];originaljob=json.loads(read(G/'input-baseline'/jobpath));newjob=json.loads(moved[jobpath]);restored=copy.deepcopy(newjob);restored['resources']['disk_paths']=originaljob['resources']['disk_paths'];restored['resources']['storage_budget']['root']=originaljob['resources']['storage_budget']['root'];ok(case+' job exact JSON inverse outside two roots',restored==originaljob)
 ok(case+' complete new workspace',json.loads(moved[exp['inputs']['execution_workspace']['path']])=={'root':fresh,'ledger':fresh+'/research_runs','artifacts':fresh+'/research_artifacts','git_common':fresh+'/.git'})
 for role,item in bound['case_contract']['additional_inputs'].items():
  ref=bound['experiment']['inputs'][role];raw=moved.get(ref['path'],None)
  if raw is None:raw=read(G/'input-baseline'/ref['path'])
  ok(case+' complete case contract '+role,item['reference']=={'path':ref['path'],'bytes':len(raw),'sha256':sha(raw)} and sha(raw)==ref['sha256'])
 for role,r in draft['roles'].items():
  if r is not None:
   ref=r['historical_reference'];ok(case+' original role '+role,r['future_reference'] is None and read(G/'role-baseline'/case/(role+'.json'))==read(P.CAP/ref['path']) and sha(read(P.CAP/ref['path']))==ref['sha256'])
def refuses(name,fn):
 try:fn()
 except (ValueError,KeyError):checks.append(name)
 else:raise AssertionError(name)
for root in (str(P.CAP),str(P.CAP/'descendant'),'relative','/tmp/../noncanonical'):
 refuses('bad root refused '+root,lambda root=root:R.rebind('success',root))
refuses('unknown case refused',lambda:R.rebind('unknown',fresh))
for v in (None,{},frozen['success'],{'status':'RELEASED','all_fields':'filled'}):refuses('release always refused '+str(type(v)),lambda v=v:P.release(v))
P.one_change(before,after)
for mode in ('missing','added','secondmutation','oldbody','unknownbody'):
 changed=dict(after)
 if mode=='missing':changed.pop(next(k for k in changed if k!=P.CHANGE))
 elif mode=='added':changed['opaque-extra.py']='0'*64
 elif mode=='secondmutation':changed[next(k for k in changed if k!=P.CHANGE)]='0'*64
 elif mode=='oldbody':changed[P.CHANGE]=P.OLD
 else:changed[P.CHANGE]='0'*64
 refuses('source delta refuses '+mode,lambda changed=changed:P.one_change(before,changed))
# Independently characterize partial helper predicates instead of inventing refusals.
for root in ('/',str(P.CAP.parent)):
 result,_=R.rebind('success',root);ok('observed ancestor-root acceptance '+root,result['capsule_root']==root);observations.append({'id':'RR1','root':root,'accepted_by_pure_rebind':True,'writes_to_root':False,'release_still_refuses':True})
smallbefore=dict(before);smallafter=dict(after);drop=next(p for p in before if p!=P.CHANGE);smallbefore.pop(drop);smallafter.pop(drop);P.one_change(smallbefore,smallafter)
observations.append({'id':'RR2','helper':'one_change','both_maps_count':198,'accepted':True,'build_checks199_separately':True})
# Return a modified owned in-memory metadata draft only; no baseline or caller input is edited.
originalread=R.read;base_draft=json.loads(read(G/'DRAFT_CASES01.json'));mut=copy.deepcopy(base_draft);mut['success']['roles']['opaque_extra']=None;mut['success']['experiment']['source_files'].pop(drop)
def altered(path):return P.encode(mut) if Path(path)==G/'DRAFT_CASES01.json' else originalread(path)
R.read=altered
try:result,_=R.rebind('success',fresh)
finally:R.read=originalread
ok('observed altered role/source metadata passes pure rebind',len(result['roles'])==16 and len(result['experiment']['source_files'])==198)
observations.append({'id':'RR3','helper':'rebind','roles':16,'source_pins':198,'accepted':True,'frozen_candidate_has_exact15and199':True,'release_still_refuses':True})
ok('no numerical or genuine research imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')) and not any(n.startswith('tradingagents') for n in sys.modules))
result={'schema_version':1,'checks':checks,'count':len(checks),'candidate_pins':pins,'actual_baseline_commit':P.HEAD,'actual_git_reads':git_calls,'source_count':199,'package_count':148,'changed_count':1,'unchanged_count':198,'C6_source_objects':26,'unique_opaque_input_paths':len(allpaths),'partial_helper_observations':observations,'model_provenance':{'actual_held_model_sha256':after['tradingagents/research/onchain_replication/model.py'],'actual_C6_model_sha256':claim['experiment']['source_files']['tradingagents/research/onchain_replication/model.py'],'financial20f_model_equality_claimed':False},'actual_native_execution':False,'actual_claims':False,'network':False,'payload_decoding':False,'numerical_imports':False,'future_release':None}
(H/'CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(len(checks),'independent recipe checks passed; partial helper observations retained')
