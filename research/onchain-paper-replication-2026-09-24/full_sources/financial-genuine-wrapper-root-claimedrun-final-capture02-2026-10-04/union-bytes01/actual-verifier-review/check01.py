import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;G=B/'financial-genuine-wrapper-root-claimedrun-outcome-binding-generation01-2026-10-04';A=B/'financial-genuine-wrapper-claimedrun-outcome-binding-preparation02-2026-10-04';V=B/'financial-genuine-wrapper-claimedrun-outcome-binding-review02-2026-10-04';checks=[]
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def raw(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2,'regular bounded '+str(p));b=p.read_bytes();t=p.lstat();ck((s.st_ino,s.st_dev,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_dev,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable '+str(p));return b
def sha(b):return hashlib.sha256(b).hexdigest()
def obj(p):return json.loads(raw(p))
def tree(root):
 rows=[]
 def scan(p):
  for q in sorted(p.iterdir()):
   s=q.lstat();r={'path':q.relative_to(root).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):r['kind']='directory'
   elif stat.S_ISREG(s.st_mode):b=raw(q);r.update(kind='file',bytes=len(b),sha256=sha(b))
   elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
   else:raise AssertionError('unexpected member')
   rows.append(r)
   if r['kind']=='directory':scan(q)
 scan(root);return sorted(rows,key=lambda r:r['path'])
manifest=obj(G/'MANIFEST_ACTUAL04.json');ck(sha(raw(G/'MANIFEST_ACTUAL04.json'))=='cd53521c5abe8d90ae7511e1f7c2d7fe574c5e59e8fa7a983d7b09392cbe4f5e','actual complete manifest pin');rows=tree(G);ck([r for r in rows if r['path']!='MANIFEST_ACTUAL04.json']==manifest['members'],'complete actual generation tree');ck(len(manifest['members'])==141,'141 original census members');ck(stat.S_IMODE(G.stat().st_mode)==manifest['root_mode'],'root mode')
# Original author tree remains byte/mode equivalent, including original manifest.
for r in tree(A):
 p=G/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'adopted mode '+r['path'])
 if r['kind']=='file':ck(sha(raw(p))==r['sha256'],'adopted body '+r['path'])
 elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'adopted directory')
 else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal link')
ck(sha(raw(V/'MANIFEST01.json'))=='702ad653ed11f67810440c1d193302cc33e9a8ade505d1202cc812bc7291395e','independent source review')
D=G/'generated-claimedrun01';qraw=raw(D/'REQUEST_FINAL03.json');q=json.loads(qraw);Q=Path(q['parent_root']);C=Path(q['capsule_root']);ck(sha(qraw)=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','actual request hash');ck(raw(Q/'REQUEST_FINAL03.json')==qraw,'actual installed request bytes');ck(sha(raw(Q/'parent01.py'))==q['caller_sha256']=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','actual Parent body')
for n,pin in q['helper_hashes'].items():ck(sha(raw(Q/n))==pin==sha(raw(G/n)),'actual helper '+n)
proof_origins={'cumulative':B/'financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04'/'EXTENSION_REVIEW01.json','independent_source_input_runtime':B/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04'/'INDEPENDENT_SOURCE_INPUT_RUNTIME01.json','full_recovery':B/'financial-genuine-wrapper-claimedrun-source339-actual-flat-review01-2026-10-04'/'FULL_SOURCE_RECOVERY01.json'}
for role,ref in q['proofs'].items():
 p=Path(ref['path']);ck(p.resolve()==p and p.is_relative_to(Q),'contained canonical proof');body=raw(p);ck(sha(body)==ref['sha256'],'actual proof '+role);ck(body==raw(proof_origins[role]),'genuine original independent proof '+role)
fref=q['final_review'];release=raw(Path(fref['path']));ck(sha(release)==fref['sha256']=='95dadb68b74693212dece8b363156ddc5d98c4b4726a9c50577d2655bb8f3c38','actual seven field review hash');ck(release==raw(B/'financial-genuine-wrapper-claimedrun-parent-final-release-review01-2026-10-04'/'RELEASE01.json'),'actual independent release origin')
# Pure genuine validator only; no binder rerun, preflight, admit, launch or outcome execution.
import importlib.util,sys
sys.path.insert(0,str(G));spec=importlib.util.spec_from_file_location('actual_parent_validator_only',G/'accepted_parent01.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);ck(P.validate_release(q)==json.loads(release),'genuine original release validation')
gate_raw=raw(C/q['registration']);gate=json.loads(gate_raw);e=gate['experiments'][q['identity']];ck(sha(gate_raw)==q['registration_sha256'],'current actual gate');ck(e['source_files']==q['source_files'] and len(q['source_files'])==338,'338 exact pins')
for n,pin in q['source_files'].items():ck(sha(raw(C/n))==pin,'actual current source '+n)
ck({k:v['sha256'] for k,v in e['inputs'].items()}==q['input_hashes'] and len(q['input_hashes'])==8,'actual eight inputs')
for role,ref in e['inputs'].items():ck(sha(raw(C/ref['path']))==ref['sha256'],'actual input '+role)
ck(obj(C/e['inputs']['runtime_mapping']['path'])==q['runtime_mapping'] and len(q['runtime_mapping']['distribution_records'])==251,'actual runtime251 metadata')
head=raw(C/'.git/HEAD').decode().strip();current=raw(C/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;ck(current==q['source']==q['design_source']=='0a2e7639b42b9423b90743feadcda4078aa21816','actual current source HEAD')
ck(not os.path.lexists(C/'research_runs'/q['identity']),'fresh claim absent')
source=raw(D/'verifier01.py');ck(sha(source)=='14089451a225aa541eb6faf30c78cb31c79b1380d7ef54d77e895575e3ce250c','actual emitted verifier');inv=obj(D/'INVERSE01.json')['edits'];ck(len(inv)==7,'seven edits');back=source.decode()
for edit in reversed(inv):ck(back.count(edit['new'])==1,'unique inverse');back=back.replace(edit['new'],edit['old'])
original=raw(G/'original-verifier03.py');ck(back.encode()==original and ast.dump(ast.parse(back))==ast.dump(ast.parse(original)),'full byte AST inverse')
# Independently reconstruct seven edits from actual literals and accepted pinned rewrite data, never invoke generator.
binder_tree=ast.parse(raw(G/'bind01.py'));edits=ast.literal_eval(next(n.value for n in binder_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ACCOUNTING_EDITS' for t in n.targets)))
oldq='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc';olds='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0';expected=[("QHASH='"+oldq+"'","QHASH='"+sha(qraw)+"'"),("par.value('REQUEST_FINAL03.json',QHASH)","par.value('REQUEST_FINAL03.json',QHASH)"),("source==q['design_source']=='"+olds+"'","source==q['design_source']=='"+q['source']+"'"),*edits];expected=[{'old':a,'new':b} for a,b in expected if a!=b];ck(inv==expected,'exact actual complete rewrite list');forward=original.decode()
for r in expected:forward=forward.replace(r['old'],r['new'])
ck(forward.encode()==source,'actual deterministic reconstructed emission')
binding=obj(D/'BINDING01.json');ck(sha(raw(D/'BINDING01.json'))=='57e3b72754668f3be5d1611475b9c29be3fabd91ffe71c5cad60792fa4881989','actual binding pin');ck(binding=={'source':q['source'],'identity':q['identity'],'parent_source_sha256':q['caller_sha256'],'actual_request_sha256':sha(qraw),'final_parent_review':q['final_review'],'verifier_sha256':sha(source),'outcome_classified':False,'numerical_authority':False},'exact binding semantics')
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):ck(raw(D/n)==raw(G/n),'generated unchanged helper '+n)
receipt=obj(G/'ACTUAL_GENERATION02.json');ck(receipt['actual_tool_chunk']=='ea1d79' and receipt['actual_tool_exit']==0,'actual emit terminal');ck(all(receipt[k] is None for k in ('observed_pid','observed_start_ticks','original_process_group_history','actual_tool_session')),'unobserved original process history remains null');ck(sha(raw(G/'ACTUAL_GENERATION01.out'))==receipt['raw_stdout_sha256'] and raw(G/'ACTUAL_GENERATION01.out').decode().strip()==str(D),'actual stdout');ck(raw(G/'ACTUAL_GENERATION01.err')==b'','empty stderr');fail=obj(G/'MANIFEST_FAILED03.json');ck(fail['actual_exit']==1 and fail['actual_tool_chunk']=='06f232' and fail['binder_or_outcome_rerun'] is False and fail['new_science_claim'] is False,'separate census failure preserved')
ck(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numerical imports');out={'decision':'ACCEPTED_ACTUAL_BINDING_SOURCE_ONLY','checks':len(checks),'check_names':checks,'actual_generation_manifest_sha256':sha(raw(G/'MANIFEST_ACTUAL04.json')),'actual_request_sha256':sha(qraw),'actual_verifier_sha256':sha(source),'actual_binding_sha256':sha(raw(D/'BINDING01.json')),'original_process_history':None,'outcome_executed':False,'binder_rerun':False,'numerical_release':False};(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='check_names'}))
