from pathlib import Path
import ast,copy,types,json,hashlib,difflib
H=Path('research/onchain-paper-replication-2026-09-24/full_sources');B=H/'matching-compiled-two-attribute-caller-candidate02-2026-10-11';N=H/'matching-compiled-two-attribute-caller-candidate03-2026-10-11';O=H/'matching-compiled-two-attribute-caller-source-review03-2026-10-11';refs={};checks=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[str(p)]=r;return r
def read(p):ref(p);return json.loads(p.read_text())
def ck(x,s):assert x,s;checks.append(s)
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
m=read(N/'MANIFEST03.json');ck(refs[str(N/'MANIFEST03.json')]['sha256']=='fafd78521d0576756018c3b73c1f1adf809490fa3220112b54f3a3b2075a8b4a','frozen03')
for n,r in m['files'].items():a=ref(N/n);ck(all(a[k]==r[k] for k in ('sha256','bytes')),'member '+n)
req=read(N/'SOURCE_REQUIREMENTS01.json');changed=[];fw='';iv=''
for path,r in req.items():
 n=Path(path).name;a=ref(N/n);ck(all(a[k]==r[k] for k in ('bytes','sha256')),'exact requirement '+n)
 old=(B/n).read_text();new=(N/n).read_text();ref(B/n)
 if old!=new:
  changed.append(n);fw+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=n,tofile=n));iv+=''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=n,tofile=n))
ck(changed==['batched_numeric_reuse.py','compiled_edge_owner.py'],'only owner and memo changed eight route bodies same');ck(fw==(N/'FORWARD.patch').read_text() and iv==(N/'INVERSE.patch').read_text(),'exact complete forward inverse')
old=(B/'compiled_edge_owner.py').read_text();new=(N/'compiled_edge_owner.py').read_text()
a=old[old.index('                import fcntl,importlib.util'):old.index('                view=memoryview(raw)')];b=new[new.index("                require(sys.platform=='linux'"):new.index('                view=memoryview(raw)')]
z=new.replace(b,a).replace('fcntl.fcntl(fd,1033,seals)','fcntl.fcntl(fd,fcntl.F_ADD_SEALS,seals)').replace('fcntl.fcntl(fd,1034)','fcntl.fcntl(fd,fcntl.F_GET_SEALS)')
ck(z==old and ast.dump(ast.parse(z))==ast.dump(ast.parse(old)),'exact primitive-only literal AST inverse')
nh=ref(N/'compiled_edge_owner.py')['sha256'];oh=ref(B/'compiled_edge_owner.py')['sha256'];ck((N/'batched_numeric_reuse.py').read_text().replace(nh,oh)==(B/'batched_numeric_reuse.py').read_text(),'sole memo owner pin');ck((N/'POLICY_TEMPLATE01.json').read_bytes()==(B/'POLICY_TEMPLATE01.json').read_bytes(),'exact policy unchanged')
# Reuse only author inert exercise definition, with exact candidate AST prefix; no author top-level or native imports.
tree=ast.parse(new)
def find(name):return copy.deepcopy(next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name))
def require(v,n):
 if not v:raise ValueError(n)
prefix=next(n for n in find('acquire').body if isinstance(n,ast.Try));end=next(i for i,n in enumerate(prefix.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='info');prefix.body=prefix.body[:end];prefix.body=[ast.Pass() if isinstance(n,ast.Import) else n for n in prefix.body]
exercise=next(n for n in ast.parse((N/'check_source01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='exercise');env={'ast':ast,'copy':copy,'types':types,'find':find,'prefix':prefix,'require':require};exec(compile(ast.Module(body=[exercise],type_ignores=[]),'<reused-inert-exercise>','exec'),env)
run=env['exercise'];fd,error,events,create,c=run(allocated=0);ck(fd==0 and error is None,'valid descriptor zero retained');ck(create.argtypes==(c.c_char_p,c.c_uint) and create.restype is c.c_int,'typed unsigned flags signed return');ck(events[:2]==[('libc',None,{'use_errno':True}),('create',b'uncached-edge',3)],'lookup errno flags');ck(('fcntl',0,1033,(15,)) in events and ('fcntl',0,1034,()) in events,'seal commands mask')
_,error,events,*_=run(allocated=-1);ck(isinstance(error,OSError) and error.errno==38 and not any(x[0] in ('write','close','fcntl') for x in events),'negative return never fd-owned')
fatal=MemoryError('injected write');_,error,events,*_=run(allocated=0,write_error=fatal,close_error_value=OSError('injected close'));ck(error is fatal and events.count(('close',0))==1,'fd0 fatal primary preserved cleanup once')
_,error,events,*_=run(seals=0);ck(isinstance(error,ValueError) and events.count(('close',7))==1,'seal mismatch fatal closed')
_,error,events,*_=run(platform='darwin');ck(isinstance(error,ValueError) and not events,'nonLinux no lookup')
P=H/'pilot34-linux-memfd-compatibility-probe01-2026-10-11';probe=read(P/'PROBE01.json');tool=read(P/'ACTUAL_TOOL_RECEIPTS01.json');ref(P/'ACTUAL_INLINE_PROBE_SOURCE01.py');header=read(P/'ACTUAL_HEADER_READBACK01.json')
ck(json.loads(tool['probe']['output'])==probe and tool['probe']['exit_code']==0 and tool['not_a_prelaunch_source_freeze'],'actual Root probe receipt join not prefreeze')
ck(probe['actual_kernel_seals']==15 and probe['fd_closed'] and probe['flags']==3 and probe['F_ADD_SEALS']==1033 and probe['F_GET_SEALS']==1034 and probe['refusals']==['write','grow','shrink'],'actual existing kernel proof values')
prior=ref(H/'matching-compiled-two-attribute-caller-source-review02-2026-10-11/REVIEW02.json');ck(prior['sha256']=='bd72989c22ccb9ac10f8409359fcd972e66f22225f789d3c1570a38a80681a7b','accepted extent review reused')
review={'decision':'accepted','scope':'Exact caller03 Linux primitive compatibility source and prospective entry only.','checks':checks,'references':refs,'source_owner_sha256':nh,'unchanged_modules':8,'preserved':['All original body/runtime/ABI/path seals/currentness checks, owner captured cleanup and primary refusal.','Exact adapter, numerical bodies and21920 genuine caller extent.','Typed libc call accepts descriptor0, rejects negativeerrno before publishing ownership; valid fd assigned before fallible work.'],'limits':['No actual ctypes/kernel/native/scientific import, real Owner/Run/Admission, numerical execution or performance measurement by this reviewer.','Existing Root41B kernel probe is genuine supplied tool evidence retained after execution, not a pre-frozen-source run or complete library-loader proof.','Actual qualified native caller execution and current source/policy/runtime admission remain pending.','This source review is not installation or empirical release.'],'native_execution_released':False}
dump(O/'REVIEW03.json',review);(O/'REPORT.md').write_text('Accepted narrow caller03 Linux compatibility source. Exact literal/AST inverse limits changes to typed libc memfd creation and Linux seal constants; memo owner hash is the only other source change, eight route/numerical bodies unchanged. Independent controls using exact acquisition prefix with inert stand-ins cover fd0, negativeerrno, fatal primary+close failure, seal mismatch and nonLinux refusal. Existing Root kernel probe and supplied tool receipt agree; source was retained after execution and is not a prefreeze claim. Real owner/library/native qualification remains pending; no numerical/native operations executed here.\n');dump(O/'MANIFEST03.json',{'status':'FROZEN_SOURCE_ONLY_LINUX_COMPATIBILITY_REVIEW','files':{p.name:ref(p) for p in O.iterdir()}});print(json.dumps({'review':ref(O/'REVIEW03.json'),'manifest':ref(O/'MANIFEST03.json'),'checks':len(checks)}))
