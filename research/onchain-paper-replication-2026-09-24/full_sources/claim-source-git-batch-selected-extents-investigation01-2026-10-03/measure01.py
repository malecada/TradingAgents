"""Only explicit claim metadata and registered source/charter Git blobs; no claims execute."""
import ast,hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
IMP=BASE/'original-import-native-successor-preparation06-2026-10-03/capsule04'
SCI=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-01/source')
CAND=BASE/'claim-source-git-batch-candidate01-2026-10-03'
TARGET='tradingagents/research/verify.py';ENV={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
def sha(b):return hashlib.sha256(b).hexdigest()
refs={}
def pin(p):
 b=p.read_bytes();refs[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def git(root,*args,input=None):return subprocess.run(['git',*args],cwd=root,env=ENV,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30)
def blob(root,commit,path):
 assert not Path(path).is_absolute() and '..' not in Path(path).parts and not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in Path(path).parts)
 p=git(root,'cat-file','blob',commit+':'+path);return p.stdout
candidate=pin(CAND/'candidate01.py');assert sha(candidate)=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
pin(CAND/'MANIFEST01.json');pin(BASE/'claim-source-git-batch-review01-2026-10-03/REVIEW_BATCH01.md')
# Only pure selected request encoder; no transport/verifier/claim API executed.
nodes=[n for n in ast.parse(candidate).body if isinstance(n,ast.FunctionDef) and n.name=='_source_request']
import re
ns={'Path':Path,'re':re,'_GIT_REQUEST':65536};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-pure-request-encoder','exec'),ns)
def inventory(root,commit,pinned,label):
 rows=[];groups=[];current=[];request=b''
 def flush():
  nonlocal current,request
  if not current:return
  result=git(root,'cat-file','--batch',input=request);raw=result.stdout;offset=0
  for row in current:
   end=raw.index(b'\n',offset);head=raw[offset:end];oid,kind,size=head.split();size=int(size);assert kind==b'blob' and len(oid)==40 and size<=8388608 and len(head)+1<=128
   value=raw[end+1:end+1+size];assert len(value)==size and raw[end+1+size:end+2+size]==b'\n' and sha(value)==row['sha256']
   row.update(bytes=size,git_object=oid.decode(),framing_bytes=len(head)+2,old_verify_bytes=size if row['path']==TARGET else None)
   offset=end+2+size
  assert offset==len(raw)
  g={'rows':len(current),'request_bytes':len(request),'body_bytes':sum(r['bytes'] for r in current),'framing_bytes':sum(r['framing_bytes'] for r in current),'stdout_bytes':len(raw),'stderr_bytes':len(result.stderr),'paths':[r['path'] for r in current]}
  assert g['rows']<=128 and g['request_bytes']<=65536 and g['stdout_bytes']<=8388608+16384 and g['stderr_bytes']<=65536
  groups.append(g);current=[];request=b''
 for path,h in pinned.items():
  expression,part=ns['_source_request'](commit,path);assert part is not None,'unexpected selected fallback path'
  if len(current)==128 or len(request)+len(part)>65536:flush()
  row={'path':path,'commit':commit,'sha256':h,'request_bytes':len(part),'expression_bytes':len(os.fsencode(expression))};rows.append(row);current.append(row);request+=part
 flush()
 return {'label':label,'commit':commit,'rows':rows,'groups':groups,'source_plus_charter_rows':len(rows),'body_bytes':sum(r['bytes'] for r in rows),'package_rows':sum(r['path'].startswith('tradingagents/') for r in rows),'package_bytes':sum(r['bytes'] for r in rows if r['path'].startswith('tradingagents/')),'fallback_rows':0}
results=[]
for index,p in enumerate(sorted((IMP/'research_runs').glob('original-import-native-success-*/claim.json')),1):
 claim=json.loads(pin(p));assert claim['source']==claim['design_source']
 regraw=blob(IMP,claim['source'],claim['registration']);assert sha(regraw)==claim['registration_sha256'];reg=json.loads(regraw);exp=reg['experiments'][claim['experiment_id']]
 assert exp==claim['experiment'] and reg['families'][exp['family']]==claim['family']
 pinned=dict(exp['source_files'])
 for k in ('charter','selection'):
  if exp.get(k):pinned[exp[k]['path']]=exp[k]['sha256']
 assert len(pinned)==[154,157,160,163][index-1]
 r=inventory(IMP,claim['source'],pinned,claim['experiment_id']);r['claim_sha256']=sha(p.read_bytes());r['registration_sha256']=sha(regraw);r['actual_terminal']='failed';assert (p.parent/'failed.json').is_file();r['source_rows']=len(exp['source_files']);results.append(r)
reg=json.loads(pin(SCI/'cold-registration.json'));exp=reg['experiments']['compact-cold-inputs-20261003-01'];head=git(SCI,'rev-parse','HEAD').stdout.decode().strip();assert head=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e'
assert blob(SCI,head,'cold-registration.json')==(SCI/'cold-registration.json').read_bytes()
pinned=dict(exp['source_files']);pinned[exp['charter']['path']]=exp['charter']['sha256'];assert len(pinned)==196
r=inventory(SCI,head,pinned,'SCI-sourceA-unclaimed-prospective');r['source_rows']=195;results.append(r)
# Hypothetical source byte substitution only: no new commit or authority.
for r in results:
 old=next(x for x in r['rows'] if x['path']==TARGET);delta=len(candidate)-old['bytes'];g=next(g for g in r['groups'] if TARGET in g['paths']);framing_delta=len(str(len(candidate)))-len(str(old['bytes']))
 r['candidate_delta']={'old_verify_bytes':old['bytes'],'new_verify_bytes':len(candidate),'body_delta_bytes':delta,'framing_delta_bytes':framing_delta,'affected_group_stdout_if_same_order':g['stdout_bytes']+delta+framing_delta,'package_bytes_if_inline_substitution':r['package_bytes']+delta,'selected_total_bytes_if_inline_substitution':r['body_bytes']+delta,'qualification':'Counterfactual same paths/order only; no successor source/registration/charter bytes or commit invented.'}
 assert g['stdout_bytes']+delta+framing_delta<=8388608+16384
# Exact route classes, byte encoding only; no Git process or new file.
classes={}
for label,path in [('ordinary','path.py'),('LF','line\nname'),('CR','cr\rname'),('nonutf8','name-\udcff'),('oversized_line','x'*65500)]:
 e,q=ns['_source_request'](head,path);classes[label]={'expression_bytes':len(os.fsencode(e)),'batch':q is not None,'fallback_argv_within_cap':len(os.fsencode(e))<=131072}
assert classes['nonutf8']['batch'] and not classes['LF']['batch'] and not classes['CR']['batch'] and not classes['oversized_line']['batch']
out={'status':'authenticated-source-extent-only','limits':{'requests':128,'request_bytes':65536,'per_blob_bytes':8388608,'stdout_bytes':8404992,'stderr_bytes':65536,'fallback_expression_bytes':131072,'monitored_seconds':10,'cleanup_wait_seconds':5},'inventories':results,'path_classes':classes,'offline':{'git_no_lazy_fetch':'1','git_terminal_prompt':'0','network_calls':0,'all_requested_objects_available':True},'qualification':'No candidate transport/verifier/admission/Owner/claim executed; no timing/capacity inference.'}
(HERE/'readback01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');(HERE/'source_refs01.json').write_text(json.dumps(refs,indent=2,sort_keys=True)+'\n')
for r in results:print(r['label'],r['source_plus_charter_rows'],r['body_bytes'],[(g['rows'],g['request_bytes'],g['stdout_bytes']) for g in r['groups']],r['candidate_delta'])
print('PASS selected extents; fallback encoding classes',classes)
