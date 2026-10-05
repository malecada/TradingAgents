from pathlib import Path
import ast,hashlib,json,os,stat,sys,subprocess
O=Path(__file__).resolve().parent;F=O.parent;ROOT=F.parents[2];D=F/'financial-wrapper-compatibility-final-supplement-root02-2026-10-05';A=F/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
H=lambda b:hashlib.sha256(b).hexdigest();checks=[];observed={}
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sig(p):
 s=p.lstat();return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,h=None):
 p=Path(p);s=p.lstat();ss=sig(p);ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'regular bounded '+p.name);b=p.read_bytes();ok(ss==sig(p),'read stable '+p.name)
 if h:ok(H(b)==h,'hash '+p.name)
 observed[str(p)]={'sha256':H(b),'bytes':len(b),'signature':list(ss)};return b
q=json.loads(read(D/'ROOT_REQUEST_FINAL_SUPPLEMENT01.json','b18caea1a109acc7057af1d6d3254069b1f44f1d727419d4afec928c498defe8'))
craw=read(D/'REMOTE_CONTRACT01.json','25d35d4944ac3578ef63194398cd4099915536ec8efd77a4ee2b09e4b4586dd8');c=json.loads(craw)
selraw=read(D/'SELECTED_BODIES01.json','7bc47e8ce0304c9b79d395b021deffa835d0147d1471bd2da6ad2fc9a81c36e2');sel=json.loads(selraw)
for n,h in c['helpers'].items():
 b=read(D/n,h)
 if n!='recover01.py':ok(b==read(A/n),'immutable installed '+n)
caller=read(D/'caller_remote01.py','cf0f9c7e2f6e61cf178178150daa0c2d9b8cc2cbaa912b5793d78012513fb64d');ok(caller==read(A/'caller_remote01.py'),'exact accepted adapted caller')
sys.path[:0]=[str(D),str(D/'utilities')];import binding01 as B;import watch01 as W
R=B.R
required=B.validate(q);generated,changes=B.remote_source(q);ok(generated==read(D/'recover01.py','07664b20d47449ce90122aa657a04b3418c0f2ea1ed9eec907719258e6528302'),'actual regenerated exact source')
freeze=json.loads(read(D/'ROOT_BINDING_FREEZE01.json'));ok(changes==[tuple(x) for x in freeze['exact_generated_changes']],'literal source seams')
ok(sel=={'remote_commit':q['actual_main_commit'],'rows':[dict(path=k,**v)for k,v in sorted(required.items())]},'complete exact selection')
ok(len(required)==15 and sum(v['bytes'] for v in required.values())==486217,'selection denominator')
commit='fc5af68f3f0dce82390c17ce15ab5e14c997c279';ok(q['actual_main_commit']==c['main_commit']==sel['remote_commit']==commit,'fixed commit')
ok(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],timeout=10).decode().strip()==commit,'actual Main commit')
names=sorted(required);proc=subprocess.run(['git','-C',str(ROOT),'cat-file','--batch'],input=''.join(commit+':'+n+'\n'for n in names).encode(),capture_output=True,timeout=10,check=True);ok(len(proc.stdout)<1024**2 and not proc.stderr,'bounded committed selection');off=0;oids={}
for n in names:
 end=proc.stdout.index(b'\n',off);oid,kind,size=proc.stdout[off:end].decode().split();size=int(size);body=proc.stdout[end+1:end+1+size];off=end+2+size
 local=read(ROOT/n,required[n]['sha256']);ok(kind=='blob' and body==local and size==required[n]['bytes'],'actual committed selected body '+n);ok(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==oid,'blob OID');oids[n]=oid
ok(off==len(proc.stdout),'exact git framing')
for k in ('actual_remote_receipt','actual_restore_release','actual_selected_mode_profile'):ok(q[k] is None,'actual future remains null '+k)
for k in ('flat_release','remote_receipt','remote_root_exit','selected_mode_profile'):ok(c[k] is None,'contract future null '+k)
bundle=q['bundles'][0];capture_root=(ROOT/bundle['archive']['path']).parent;snapshot=capture_root/'snapshot';m=json.loads(read(ROOT/bundle['manifest']['path'],bundle['manifest']['sha256']));capture=json.loads(read(ROOT/bundle['capture']['path'],bundle['capture']['sha256']))
ok(R.scan(snapshot)==m,'complete capture tree modes/bodies');ok(len(m['members'])==121 and sum(r['kind']=='file'for r in m['members'])==106,'archive denominator121/106')
sink=R.Sink();R.tar_stream(snapshot,m,sink);ok(sink.count==bundle['archive']['bytes'] and sink.hash.hexdigest()==bundle['archive']['sha256'],'exact canonical PAX/gzip archive')
origins=json.loads(read(snapshot/'ORIGINS01.json'));mapped=set()
for row in origins['origins']:
 p=snapshot/row['snapshot_path'];b=read(p,row['sha256']);src=Path(row['original_path']);ok(b==read(src,row['sha256']) and len(b)==row['bytes'],'literal original body');ok(stat.S_IMODE(src.lstat().st_mode)==row['original_mode'],'actual original mode');mapped.add(row['snapshot_path'])
ok(mapped=={r['path']for r in m['members']if r['kind']=='file'}-{'ORIGINS01.json'},'all105 body origins')
for name,tree in origins['original_typed_scopes'].items():
 group=[r for r in origins['origins']if r['snapshot_path'].startswith(name+'/')];ok(bool(group),'typed origin group');first=group[0];root=Path(first['original_path'])
 for _ in Path(first['snapshot_path']).parts[1:]:root=root.parent
 ok(R.scan(root)==tree,'complete original typed scope '+name)
finalraw=read(P/'REQUEST_FINAL01.json',q['complete_final_request']['sha256']);final=json.loads(finalraw);ready=json.loads(read(P/'REQUEST_READY_FOR_REVIEW01.json','0686608eafb699c0492ba1708a7d61e6f0a6e0ffebbb4e37d9dcba319b6ca914'))
ok({k for k in final if final[k]!=ready[k]}=={'final_review'},'final fills only real review');release=json.loads(read(final['final_review']['path'],final['final_review']['sha256']));ok(H(R.encode({k:v for k,v in final.items()if k!='final_review'}))==release['contract_sha256'],'actual Parent release contract')
ok(release['proof_sha256']=={k:v['sha256']for k,v in final['proofs'].items()},'all three actual Parent proofs')
for ref in final['proofs'].values():read(ref['path'],ref['sha256'])
pf=json.loads(read(snapshot/'preflight/PARENT_FINAL_PREFLIGHT01_TOOL_EXIT.json'));ok(pf['actual_root_exit']==0,'actual preflight tool0')
for n,r in pf['streams'].items():ok(len(read(snapshot/'preflight'/n,r['sha256']))==r['bytes'],'preflight actual stream')
stdout=json.loads(read(snapshot/'preflight/PARENT_FINAL_PREFLIGHT01.stdout'));ok(stdout['metadata_bytes_read']==8267882 and stdout['status']=='PRECLAIM_METADATA_VALIDATED_NO_CLAIM' and stdout['source']==final['source'] and stdout['experiment']==final['identity'] and stdout['input_hashes']==final['input_hashes'],'actual metadata preflight result')
ok(not os.path.lexists(P/'attempt'),'financial Parent remains unused')
# Exact contract function and release-equality expression; no caller main or child.
ns={'Path':Path};tree=ast.parse(caller);nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef)and n.name in {'contract','local'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'caller_remote01.py','exec'),ns);ok(ns['contract'](c)=='REMOTE','actual caller contract')
for n in c['fresh_names']+['ROOT_FINAL_SUPPLEMENT_REMOTE02'+x for x in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')]:ok(not os.path.lexists(D/n),'fresh '+n)
for p in Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name)!=os.getpid():
  try:b=(p/'cmdline').read_bytes()
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  ok(str(D/'recover01.py').encode()not in b.split(b'\0') and str(D/'caller_remote01.py').encode()not in b.split(b'\0'),'no exact receiver/caller PID')
observation=W.census(D);ok(stat.S_IMODE(D.stat().st_mode)==0o700,'private Root')
for name,row in observed.items():ok(sig(Path(name))==tuple(row['signature']),'final sampled cohort '+Path(name).name)
result={'assertions':len(checks),'main_commit':commit,'request_sha256':H((D/'ROOT_REQUEST_FINAL_SUPPLEMENT01.json').read_bytes()),'contract_sha256':H(craw),'selection_sha256':H(selraw),'caller_sha256':H(caller),'receiver_sha256':H(generated),'selected_bodies':15,'selected_bytes':486217,'unique_selected_bodies':len(set(v['sha256']for v in required.values())),'expected_git_operations':10+len(set(v['sha256']for v in required.values()))+2*len(required),'archive_files':106,'archive_members':121,'original_body_origins':len(mapped),'observed_root':observation,'actual_preflight_charged_bytes':8267882,'actual_remote_outcome':None,'flat_entry_released':False,'numerical_authority':False}
(O/'REMOTE_CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(O/'REMOTE_READ_SET01.json').write_text(json.dumps(observed,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(result,sort_keys=True))
