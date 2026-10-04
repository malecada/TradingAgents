"""Different-author read-only Parent source/request review. No preflight/launch."""
import ast,copy,hashlib,importlib.util,json,os,re,stat,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01')
O=P.parent/'genuine-financial-wrapper-claimedrun-root-launch-20261004-01'
C=P.parent/'genuine-financial-wrapper-claimedrun-native-20261004-02/source'
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,limit=4194304):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit and p.resolve()==p,'bounded canonical body '+str(p));b=p.read_bytes();t=p.lstat();ck((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable body '+str(p));return b
def put(n,x):(H/n).write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
(H/'source').mkdir();files={}
for p in sorted(P.iterdir()):
 b=read(p);files[p.name]={'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(p.stat().st_mode)};(H/'source'/p.name).write_bytes(b)
ck(len(files)==9,'exact nine original caller preparation bodies')
ck(files['parent01.py']['sha256']=='7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3','exact Parent7f28')
ck(files['REQUEST_DRAFT01.json']['sha256']=='7f506c00e5e148ee24793412955056f71eb820059385588517fa4355c81a1763','exact draft7f506')
ck(files['SOURCE_INVERSE01.json']['sha256']=='380eb9dc277aa1de517d21357740cacd1866f5f34df1efaa5896eff0038cddbb','exact inverse380e')
s=(H/'source/parent01.py').read_text();original=read(O/'parent01.py');ck(sha(original)=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','actual predecessor5d5')
(H/'ORIGINAL_PARENT01.py').write_bytes(original)
inv=json.loads((H/'source/SOURCE_INVERSE01.json').read_text());restored=s
ck(len(inv['changes'])==7,'seven exact declared substitutions')
for change in reversed(inv['changes']):
 ck(restored.count(change['replacement'])==1,'unique inverse replacement '+change['replacement'][:70]);restored=restored.replace(change['replacement'],change['original'],1)
ck(restored.encode()==original,'full literal inverse');ck(ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False),'full AST inverse')
olddefs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newdefs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};changed=sorted(k for k in olddefs if olddefs[k]!=newdefs[k]);ck(changed==['preflight','validate_release'] and set(olddefs)==set(newdefs),'only two context functions differ')
for name,pin in inv['six_helpers_unchanged'].items():ck(files[name]['sha256']==pin==sha(read(O/name)),'unchanged original helper '+name)
# Root immutable Main preparation has the same nine bytes; authenticate its complete manifest.
prep=B/'financial-wrapper-complete100-root-parent-preparation01-2026-10-04';mb=read(prep/'MANIFEST01.json');ck(sha(mb)=='bed95bcde080c4d7a083d76f152c4b1048add33dbbfac12253a6a60480229a53','actual Root Main manifest');(H/'ROOT_PREPARATION_MANIFEST01.json').write_bytes(mb)
for name,info in files.items():ck(sha(read(prep/name))==info['sha256'],'Main preservation copy '+name)
q=json.loads((H/'source/REQUEST_DRAFT01.json').read_text());identity=q['identity'];ck(q['source']==q['design_source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207','actual source design binding')
head=subprocess.run(['git','-C',str(C),'rev-parse','HEAD'],capture_output=True,check=True,timeout=10).stdout.decode().strip();ck(head==q['source'],'actual current Source HEAD')
tree=subprocess.run(['git','-C',str(C),'ls-tree','-rz','--full-tree',q['source']],capture_output=True,check=True,timeout=10).stdout;rows=[]
for item in tree.split(b'\0'):
 if not item:continue
 meta,path=item.split(b'\t');mode,kind,oid=meta.decode().split();name=path.decode();ck(kind=='blob' and mode in ('100644','100755'),'ordinary source blob')
 b=read(C/name);ck(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual source Git/blob '+name);ck(bool((C/name).stat().st_mode&0o111)==(mode=='100755'),'source executable class '+name)
 if name!=q['registration']:ck(q['source_files'].get(name)==sha(b),'request full source pin '+name)
 rows.append({'path':name,'git_mode':mode,'oid':oid,'sha256':sha(b),'bytes':len(b)})
ck(len(rows)==339 and len(q['source_files'])==338 and set(q['source_files'])=={r['path'] for r in rows}-{q['registration']},'actual339/338 self-gate exclusion only')
graw=read(C/q['registration']);g=json.loads(graw);ck(sha(graw)==q['registration_sha256']=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','actual exact reference gate');ex=g['experiments'][identity];ck(ex['parent'] is None and ex['source_files']==q['source_files'],'independent reference parentNone/source map')
ck(identity=='financial-wrapper-classification-eager-complete100-20261003-01' and q['expected_phase']=='complete100','original next identity/phase')
inputs={}
for role,ref in ex['inputs'].items():
 b=read(C/ref['path']);ck(sha(b)==ref['sha256']==q['input_hashes'][role],'actual role '+role);inputs[role]=json.loads(b)
ck(len(inputs)==8 and inputs['wrapper_plan']['prior_input'] is None and inputs['wrapper_plan']['reference_input'] is None and inputs['wrapper_plan']['phase']=='complete100','eight roles independent full100 plan')
ck(inputs['runtime_mapping']==q['runtime_mapping'] and len(q['runtime_mapping']['distribution_records'])==251,'runtime251 declaration exact')
ck(inputs['training']['epochs']==100 and inputs['training']['batch_size']==16 and inputs['model']['lookback_days']==28,'original method100/batch16/lookback28')
ck(len(inputs['source_closure']['installed'])==194,'original194 implementation')
for p,h in inputs['source_closure']['installed'].items():ck(q['source_files'][p]==h,'scientific closure '+p)
claims=[]
for who,cp,fp in [('financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'),('financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01','d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558')]:
 cr=read(C/'research_runs'/who/'claim.json');fr=read(C/'research_runs'/who/'failed.json');ck(sha(cr)==cp and sha(fr)==fp and not os.path.lexists(C/'research_runs'/who/'complete.json'),'both immutable FAILED histories '+who);v=json.loads(cr);f=json.loads(fr);ck(f['claim_sha256']==cp and f['status']=='failed' and f['experiment_id']==who,'actual terminal join '+who);claims.append({'identity':who,'claim_sha256':cp,'failed_sha256':fp,'effective_attempt_budget':v['effective_attempt_budget']})
ck(len(list((C/'research_runs').glob('*/claim.json')))==2 and max(r['effective_attempt_budget'] for r in claims)==19,'spent2 highest19')
for p in (C/'research_runs'/identity,C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity,P/'attempt'):ck(not os.path.lexists(p),'fresh actual namespace '+str(p))
# Actual prior read-only admission evidence, no reexecution.
a=Path(q['proofs']['independent_source_input_runtime']['path']);ab=read(a);ck(sha(ab)==q['proofs']['independent_source_input_runtime']['sha256']=='6a3b48b546ccbd10e1176cc1b5b06f0143934766778761655fdc2a22d60b4473','genuine actual read-only admission');ad=json.loads(ab);(H/'ACTUAL_ADMISSION01.json').write_bytes(ab)
ck(ad['actual_calls']==1 and ad['actual_api']=='tradingagents.research.onchain_replication.job._admitted' and ad['source']==ad['design_source']==q['source'] and ad['experiment_id']==identity and ad['effective_attempt_budget']==19 and ad['actual_spent_claims']==2 and not ad['Owner_constructed'] and not ad['ResearchRun_start_called'],'actual admission/source/identity/no-start')
for name,ref in ad['imported_project_modules'].items():ck(Path(ref['path']).is_relative_to(C) and sha(read(Path(ref['path'])))==ref['sha256']==q['source_files'][str(Path(ref['path']).relative_to(C))],'authentic admitted module '+name)
for name in ('ACTUAL_CALL_TERMINAL01.json','admit01.py','MANIFEST01.json'):
 b=read(a.parent/name);(H/('ADMISSION_'+name)).write_bytes(b)
terminal=json.loads((H/'ADMISSION_ACTUAL_CALL_TERMINAL01.json').read_text());ck(terminal['actual_readback_sha256']==sha(ab) and terminal['actual_exec_return_exit_code']==0 and terminal['actual_OS_PID'] is None and terminal['PID_start_ticks'] is None,'original actual admission terminal retains null process history')
# Import ONLY unchanged stdlib byte utilities from owned copies. Extract Parent pure validator.
sys.path.insert(0,str(H/'source'));spec=importlib.util.spec_from_file_location('review_R',H/'source/recovery04.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ns={'Path':Path,'hashlib':hashlib,'json':json,'re':re,'R':R,'CAP':C,'PARENT':P,'IDENTITY':identity,'PROOFS':{'cumulative','full_recovery','independent_source_input_runtime'}}
functions={'sha','require','reference','contract','validate_release','stream_hash'};nodes=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name in functions];ns.update(os=os,stat=stat,time=time);exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_parent_selected_stdlib_functions','exec'),ns)
refusals=[]
def refuse(name,v):
 try:ns['validate_release'](v)
 except (ValueError,TypeError,KeyError) as e:refusals.append({'case':name,'type':type(e).__name__,'reason':str(e)})
 else:raise AssertionError('unexpected release '+name)
refuse('unaltered actual DRAFT_NOT_RELEASED',copy.deepcopy(q))
v=copy.deepcopy(q);v['status']='RELEASED_ONE_USE_FINANCIAL_PARENT';refuse('status-only mutation retains null final review',v)
# Substitute an actual existing receipt in the wrong role, solely a negative control.
v['final_review']=copy.deepcopy(q['proofs']['cumulative']);refuse('real wrong-role review cannot bypass null full recovery',v)
for key,bad in [('source','0a2e7639b42b9423b90743feadcda4078aa21816'),('design_source','0a2e7639b42b9423b90743feadcda4078aa21816'),('identity','financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'),('expected_phase','interrupt1'),('registration_sha256','0'*64),('parent_root',str(O))]:
 m=copy.deepcopy(v);m[key]=bad;refuse('wrong '+key,m)
for key in ('source_files','input_hashes'):
 m=copy.deepcopy(v);m[key].pop(next(iter(m[key])));refuse('incomplete '+key,m)
m=copy.deepcopy(v);m['proofs']['full_recovery']=copy.deepcopy(q['proofs']['cumulative']);refuse('actual budget receipt reused as recovery and final review is refused',m)
ck(len(refusals)==12,'12 actual-source draft/context/refusal controls')
# Tiny real file reader mechanics; no main preflight/launch nor package import.
tiny=H/'tiny';tiny.mkdir(mode=0o700);payload=b'opaque-boundary\x00'*17;(tiny/'body').write_bytes(payload)
ck(ns['stream_hash'](tiny/'body',len(payload))==sha(payload),'actual bounded stream reader tiny body')
try:ns['stream_hash'](tiny/'body',len(payload)-1)
except ValueError:checks.append('actual stream too-small limit refusal')
else:raise AssertionError('stream cap')
ck(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')) and not any(n=='tradingagents' or n.startswith('tradingagents.') for n in sys.modules),'no numerical/project package imports')
put('READBACK01.json',{'checks':len(checks),'check_names':checks,'parent_files':files,'source_records':rows,'claims':claims,'changed_AST_functions':changed,'refusal_controls':refusals,'actual_project_runtime_imported_here':False,'actual_preflight_admission_or_launch_here':False,'full_recovery':None,'final_review':None,'limitations':['existing helper resource/currentness semantics inherited; no universal race immunity claimed','source/request draft only, no source/caller external recovery','no100epoch feasibility or tensor checkpoint validation','original admission OS history stays null']})
print(json.dumps({'checks':len(checks),'refusals':len(refusals),'source_bodies':len(rows),'status':'SOURCE_DRAFT_ACCEPTED_NOT_RELEASED'}))
