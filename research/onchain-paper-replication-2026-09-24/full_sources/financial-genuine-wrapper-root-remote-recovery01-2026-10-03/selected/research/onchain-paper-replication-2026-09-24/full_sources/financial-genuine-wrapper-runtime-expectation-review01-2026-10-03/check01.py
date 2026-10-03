import ast,copy,hashlib,importlib.metadata,json,os,platform,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-runtime-expectation-investigation01-2026-10-03';sys.path.insert(0,str(P));import prepare01 as A
R=A.R;checks=[];pins=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def raw(p,pin=None):
 b=R.read(p.parent,p.name);ck(pin is None or R.digest(b)==pin,'actualpin '+p.name);pins.append({'path':str(p),'sha256':R.digest(b),'bytes':len(b)});return b
def doc(p,pin=None):return json.loads(raw(p,pin))
def refuse(f,m):
 try:f()
 except ValueError:checks.append('refused '+m)
 else:raise AssertionError(m)
m=doc(P/'MANIFEST01.json','79ef424e628cd17c389f88b0703cc9b5aca328625f6f0a96a04aa5bf78e42158');decl=set()
for r in m['members']:
 p=P/r['path'];s=p.lstat();decl.add(r['path']);ck(stat.S_IMODE(s.st_mode)==r['mode'],'manifestmode')
 if r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'manifestdirectory')
 else:b=raw(p,r['sha256']);ck(len(b)==r['bytes'] and stat.S_ISREG(s.st_mode) and s.st_nlink==1,'manifestbody')
ck(len(decl)==18 and {str(p.relative_to(P)) for p in P.rglob('*')}==decl|{'MANIFEST01.json'},'complete typed18');raw(P/'prepare01.py','876b42188d1eb21aeb2f0e91c4503ab3889423661fc9dec4d807c58b2057b4b6');ev=doc(P/'prepared01/EVIDENCE01.json','992f4e8190bdb93169b24c0e68d3a896ac3b32e4dd6bba270d370f03aa032ebf');expectedraw=raw(P/'prepared01/environment.EXPECTATION.json',A.EXPECTED_SHA);expected=json.loads(expectedraw);meta=doc(A.FLAT/'capsule-metadata.json',A.META_SHA);members={r['path']:r for r in meta['manifest']['members']};selected={}
for name in [A.EXPECTED_PATH,A.CLAIM_PATH,A.CLAIM_PATH.replace('claim.json','failed.json'),A.REG,A.JOB,A.ENV]:
 r=members[name];b=raw(A.FLAT/meta['flat_members'][name],r['sha256']);ck(r['kind']=='file' and len(b)==r['bytes'] and b==raw(A.OLD/name),'recovered/original typedbody '+name);selected[name]=b
ck(selected[A.EXPECTED_PATH]==expectedraw,'exact unchanged historical expectation');claim=json.loads(selected[A.CLAIM_PATH]);failed=json.loads(selected[A.CLAIM_PATH.replace('claim.json','failed.json')]);reg=json.loads(selected[A.REG]);ck(R.digest(selected[A.CLAIM_PATH])==A.CLAIM_SHA and claim['source']==claim['design_source']==A.OLD_SOURCE and claim['inputs']['environment']==claim['experiment']['inputs']['environment']=={'dataset':'synthetic','path':A.EXPECTED_PATH,'sha256':A.EXPECTED_SHA},'actual originalclaim input/source');ck(failed['claim_sha256']==A.CLAIM_SHA and failed['status']=='failed' and reg['experiments'][claim['experiment_id']]==claim['experiment'] and R.digest(selected[A.REG])==claim['registration_sha256'],'genuine failed/registration joins')
for n in [A.REG,A.EXPECTED_PATH,A.JOB,A.ENV]:ck(A.git(A.OLD,['show',A.OLD_SOURCE+':'+n])==selected[n],'original actual committedbody '+n)
for n in [A.JOB,A.ENV]:ck(claim['experiment']['source_files'][n]==R.digest(selected[n]),'old admittedcodehash '+n)
S=A.CURRENT;ck(A.git(S,['rev-parse','HEAD'],cap=128).decode().strip()==A.CURRENT_SOURCE,'actualcurrent44');installed=doc(F/'financial-genuine-wrapper-installed-auxiliary-review01-2026-10-03/READBACK01.json','884d6e467830ba517ead6ff48f51e7a823150bf0d8a3f4e18524def0e74db865');rows={r['path']:r for r in installed['joined']};tree=A.git(S,['ls-tree','-r','--name-only','-z',A.CURRENT_SOURCE]).split(b'\0');ck(tree[-1]==b'' and {n.decode() for n in tree[:-1]}==set(rows) and len(rows)==242,'actualcomplete242')
for n,r in rows.items():b=raw(S/n,r['sha256']);ck(len(b)==r['bytes'] and stat.S_IMODE((S/n).lstat().st_mode)==r['mode'],'all242currentbyte/mode')
names=[A.JOB,A.ENV,'tradingagents/research/lifecycle.py','tradingagents/research/onchain_replication/financial_wrapper_fixture.py'];source={}
for n in names:b=raw(S/n);ck(A.git(S,['show',A.CURRENT_SOURCE+':'+n])==b,'current actualGitcode '+n);source[n]=b
ck(source[A.ENV]==selected[A.ENV]==raw(P/'prepared01/inventory.py'),'unchangedinventory source');ck(source[A.JOB]==raw(P/'prepared01/current-job.py') and selected[A.JOB]==raw(P/'prepared01/historical-job.py'),'prepared joborigin bytes')
# Independent AST ordering of the actual source; no lifecycle or inventory invocation.
def function(body,name):return next(n for n in ast.walk(ast.parse(body)) if isinstance(n,ast.FunctionDef) and n.name==name)
worker=function(source[A.JOB],'worker');nodes=list(ast.walk(worker));calls=[n for n in nodes if isinstance(n,ast.Call)];start=next(n for n in calls if ast.unparse(n.func)=='ResearchRun.start');guard=next(n for n in calls if ast.unparse(n.func)=='resources.assert_guarded_worker');inventory=next(n for n in calls if ast.unparse(n.func)=='inventory');dispatch=next(n for n in calls if ast.unparse(n.func)=='financial_wrapper_fixture.execute');context=next(n for n in nodes if isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Call) and ast.unparse(i.context_expr.func)=='ResearchRun.start' for i in n.items));ck(guard.lineno<start.lineno<inventory.lineno<dispatch.lineno,'genuine guard before claim before live inventory before financialdispatch');ck(inventory in list(ast.walk(context)) and isinstance(context.body[0],ast.ImportFrom) and context.body[0].module=='environment','actual comparison inside genuine context');comparison=context.body[1];ck(isinstance(comparison,ast.If) and isinstance(comparison.test,ast.Compare) and isinstance(comparison.test.ops[0],ast.NotEq) and isinstance(comparison.body[0],ast.Raise),'actual mismatch raises');ck("'financial_wrapper'" in ast.unparse(inventory) and "json.loads(run.read_input(job['environment_input']))" in ast.unparse(comparison) and 'registered execution environment differs' in ast.unparse(comparison),'actualfullregisteredcomparison')
inv=function(source[A.ENV],'inventory');ck('import torch' in ast.unparse(inv) and all(x in ast.unparse(inv) for x in ['torch.cuda.is_available()', 'torch.__version__','torch.version.cuda','os.cpu_count()']),'exact live APIs not metadata substitute');fixture=source[names[3]];auth=function(fixture,'authorize');execute=function(fixture,'execute');ck('inventory(ad.root, include_torch=True)' in ast.unparse(auth) and "json.loads(run.read_input(j['environment_input']))" in ast.unparse(auth),'fixture repeats samefullinputcomparison');ck(ast.unparse(execute.body[0]).startswith('p, config, t, sources, recipe_hash = authorize('),'authorize before tensor construction');life=source[names[2]];startfn=function(life,'start');exitfn=function(life,'__exit__');failfn=function(life,'_fail_unlocked');ck('claim.json' in ast.unparse(startfn) and 'exist_ok=False' in ast.unparse(startfn),'genuine immutableclaim/noidentityreuse');ck('self._fail_unlocked' in ast.unparse(exitfn) and ast.unparse(exitfn).endswith('return False') and 'failed.json' in ast.unparse(failfn),'ordinary mismatch failedterminal no suppression')
# Current basic API observations only, never inventory(include_torch=True).
basic={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':R.digest(raw(S/'uv.lock')),'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','pyarrow','torch','scikit-learn']}};ck(basic==ev['current_basic_observations']=={k:expected[k] for k in A.BASIC} and basic['cpu_count']==12,'actual basicfields currentmatch');ck(A.expected_check(expectedraw,basic)==expected,'exact historical expectedcheck')
mapping=doc(S/'fixture_inputs/financial_wrapper_draft01/runtime_mapping.json');ck(len(mapping['distribution_records'])==251,'original251runtime pins');recordbytes=0
for row in mapping['distribution_records']:
 dist=importlib.metadata.distribution(row['name']);path=Path(dist.locate_file(next(f for f in dist.files if str(f).endswith('.dist-info/RECORD')))).resolve();ck(str(path)==row['record'] and dist.version==row['version'],'actualrecord version/path');s=path.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_size<=R.FILE,'actual bounded readonlyrecord');fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);h=hashlib.sha256();count=0
 try:
  while True:
   b=os.read(fd,65536)
   if not b:break
   count+=len(b);ck(count<=R.FILE,'record streamingbound');h.update(b)
  ck(R.sig(s)==R.sig(os.fstat(fd))==R.sig(path.lstat()) and count==s.st_size and h.hexdigest()==row['record_sha256'],'actualrecord stablehash');recordbytes+=count
 finally:os.close(fd)
ck(recordbytes<=64*1024**2,'finite metadata aggregate');draft=doc(S/'fixture_inputs/financial_wrapper_draft01/environment.DRAFT.json');ck(all(draft[k] is None for k in ['torch_version','cuda_build','cuda_available']),'original nullDraft preserved');ck(ev['current_torch_api_observed'] is False and ev['driver_unchanged_claim'] is False and ev['current_environment_equality_proven'] is False,'no false liveObservation')
for key,value in [('cpu_count',True),('cuda_available',None),('torch_version',None),('cuda_build',23)]:
 bad=copy.deepcopy(expected);bad[key]=value;refuse(lambda:A.expected_check(R.encode(bad),basic),'invalid expected '+key)
for key,value in [('cpu_count',1),('python','wrong'),('lock_sha256','0'*64)]:
 bad=copy.deepcopy(basic);bad[key]=value;refuse(lambda:A.expected_check(expectedraw,bad),'basic mismatch '+key)
ck(A.git(S,['rev-parse','HEAD'],cap=128).decode().strip()==A.CURRENT_SOURCE,'currentHEAD stable');ck(not any(n.split('.')[0] in {'torch','numpy','scipy','pandas'} for n in sys.modules),'no numerical imports');out={'decision':'ACCEPTED_HISTORICAL_EXPECTED_INPUT_REUSE_SOURCE_CONTRACT_ONLY','checks':len(checks),'expectation_sha256':A.EXPECTED_SHA,'actual_historical_claim_sha256':A.CLAIM_SHA,'historical_failed':True,'current_source':A.CURRENT_SOURCE,'current_basic_observations':basic,'current_torch_cuda_driver_observed':False,'current_full_environment_equality':False,'worker_order_lines':{'guard':guard.lineno,'claim':start.lineno,'comparison':inventory.lineno,'financial_dispatch':dispatch.lineno},'runtime_record_pins':251,'runtime_record_bytes':recordbytes,'outside_guard_torch_probe_required_by_source':False,'comparison_occurs_after_claim':True,'mismatch_spends_identity':True,'financial_slots_unreserved':18,'input_adopted_or_registration_approved':False};(O/'READBACK01.json').write_bytes(R.encode(out));(O/'PINS01.json').write_bytes(R.encode(pins));print(json.dumps(out,indent=2))
