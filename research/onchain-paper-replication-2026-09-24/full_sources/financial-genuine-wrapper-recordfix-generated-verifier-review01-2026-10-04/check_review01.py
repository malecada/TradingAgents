"""Independent emitted binding authentication; no outcome verifier or emission run."""
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'actual-binding';P=D.parent/'financial-genuine-wrapper-root-recordfix-verifier-binding01-2026-10-04';E=S/'generated-recordfix01';checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,OSError):ok(n,True);return
 raise AssertionError('accepted '+n)
ok('actual root manifest pin',sha(P/'MANIFEST_ACTUAL02.json')=='8258937c14573d2f8a51e80b1b8526e6d9da28776da3804893e54ae0436c6a93');m=json.loads((P/'MANIFEST_ACTUAL02.json').read_text());ok('complete actual root tree',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST_ACTUAL02.json'}=={r['path'] for r in m['members']});ok('39member36file denominator',len(m['members'])==39 and sum(r['kind']=='file' for r in m['members'])==36)
for r in m['members']:
 p=P/r['path'];q=S/r['path'];s=p.lstat();valid=stat.S_IMODE(s.st_mode)==r['mode']==stat.S_IMODE(q.lstat().st_mode)
 if r['kind']=='file':valid=valid and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==sha(q)==r['sha256']
 else:valid=valid and p.is_dir() and q.is_dir()
 ok('actual retained member '+r['path'],valid)
original=D.parent/'financial-genuine-wrapper-recordfix-outcome-verifier-preparation01-2026-10-04'
for row in json.loads((S/'ROOT_COPY_AUTHENTICATION01.json').read_text())['rows']:ok('original binder unchanged '+row['path'],(S/row['path']).read_bytes()==(original/row['path']).read_bytes() and sha(S/row['path'])==row['sha256'])
ok('original reference manifest preserved',sha(S/'MANIFEST01.json')=='d8b68c05c84b14332d5e1d031ebc4b7d38379bbf784ee9b1269eab63aa4505aa')
failed=json.loads((S/'MANIFEST_BUILD_FAILURE01.json').read_text());ok('separate Root manifest failure retained',failed['actual_exit']==1 and failed['actual_generator_not_rerun'] is True and failed['actual_tool']=='efec9c')
terminal=json.loads((S/'ACTUAL_GENERATION_TERMINAL01.json').read_text());ok('actual generation terminal/tool and streams',terminal['actual_exit']==0 and terminal['actual_tool']=='b4d2cb' and terminal['actual_stdout_sha256']==sha(S/'ACTUAL_GENERATION01.out') and terminal['actual_stderr_sha256']==sha(S/'ACTUAL_GENERATION01.err') and terminal['numerical_or_outcome_executed'] is False)
sys.path.insert(0,str(S));spec=importlib.util.spec_from_file_location('independent_actual_binding',S/'bind01.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
request=Path(B.PARENT)/'REQUEST_FINAL02.json';pin='28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e';ok('actual installed/generated request exact',sha(request)==sha(E/'REQUEST_FINAL02.json')==pin)
# Genuine accepted binder authentication and pure byte reconstruction only. No emit/main.
raw,q=B.authenticate(request,pin);constructed=B.generate(request,pin);ok('genuine read-only authentication returns actual request',raw==request.read_bytes());ok('exact emitted verifier hash',sha(E/'verifier01.py')=='02eb149abcb8870a6f6311eea74a2e08876c23aaf20cc991fb090e1012760405');ok('exact emitted binding hash',sha(E/'BINDING01.json')=='e3557a4834ed638806aad2a3e9559913c37794ef550aa218c9455f7e55f23edc');ok('actual reconstruction sourcebytes',constructed['source']==(E/'verifier01.py').read_bytes());ok('actual reconstruction requestbytes',constructed['request']==(E/'REQUEST_FINAL02.json').read_bytes());ok('actual binding full semantics',B.R.encode(constructed['binding'])==(E/'BINDING01.json').read_bytes());ok('actual inverse exact bytes',B.R.encode({'edits':constructed['inverse']})==(E/'INVERSE01.json').read_bytes())
for name in ('recovery04.py','owned_io.py','bounded_git01.py'):ok('emitted helper exact '+name,(E/name).read_bytes()==(S/name).read_bytes())
ok('exact emitted seven-file denominator',{p.name for p in E.iterdir()}=={'verifier01.py','REQUEST_FINAL02.json','BINDING01.json','INVERSE01.json','recovery04.py','owned_io.py','bounded_git01.py'})
code=(E/'verifier01.py').read_text();back=code;edits=json.loads((E/'INVERSE01.json').read_text())['edits'];ok('all three actual substitutions',len(edits)==3)
for i,e in enumerate(reversed(edits)):ok('unique actual inverse '+str(i),back.count(e['new'])==1);back=back.replace(e['new'],e['old'])
base=(S/'original-verifier03.py').read_text();ok('full byte inverse acceptedf662',back==base and sha(S/'original-verifier03.py')=='f6626d0a66dba46e6b4a314c4806a0452844fda886375f5e99e99186b2ceaa56');ok('full AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(base)))
olddefs={n.name:ast.dump(n) for n in ast.parse(base).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newdefs={n.name:ast.dump(n) for n in ast.parse(code).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name,dump in olddefs.items():
 if name!='verify':ok('unchanged accepted decision/cleanup '+name,newdefs[name]==dump)
verifier=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='verify');ok('actual new request andsource in verify',"par.value('REQUEST_FINAL02.json', QHASH)" in ast.unparse(verifier) and B.SOURCE in ast.unparse(verifier));ok('actual new QHASH',next(ast.literal_eval(n.value) for n in ast.parse(code).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='QHASH' for t in n.targets))==pin)
# Original actual Parent/proofs are captured as metadata only, with originals untouched.
evidence=D/'actual-parent-metadata';evidence.mkdir();proofrows=[]
for role,ref in [*q['proofs'].items(),('final_review',q['final_review'])]:
 p=Path(ref['path']);b=B.R.read(p.parent,p.name);ok('actual proof pin '+role,hashlib.sha256(b).hexdigest()==ref['sha256'] and p.is_relative_to(Path(B.PARENT)));(evidence/p.name).write_bytes(b);proofrows.append({'role':role,'actual_path':str(p),'sha256':ref['sha256'],'bytes':len(b)})
parent=B.prepared();actual_review=parent.validate_release(q);ok('actual genuine final reviewer contract',actual_review['contract_sha256']==parent.contract(q) and actual_review['proof_sha256']=={r['role']:r['sha256'] for r in proofrows if r['role']!='final_review'});ok('installed exact caller body',sha(Path(B.PARENT)/'parent01.py')==B.PARENT_HASH)
for name,h in q['helper_hashes'].items():ok('installed exact helper '+name,sha(Path(B.PARENT)/name)==h==sha(S/name))
cap=Path(B.CAP);git=subprocess.run(['git','-C',str(cap),'rev-parse','HEAD'],env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1'},stdin=subprocess.DEVNULL,capture_output=True,timeout=10,check=True);head=git.stdout.decode().strip();ok('actual current source649HEAD',head==q['source']==q['design_source']==B.SOURCE)
gate=B.R.read(cap,q['registration']);ok('actual fixed gate hash',hashlib.sha256(gate).hexdigest()==q['registration_sha256']=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a');exp=json.loads(gate)['experiments'][q['identity']];ok('actual selected324 source map',exp['source_files']==q['source_files'] and len(q['source_files'])==324)
for name,h in q['source_files'].items():ok('current exact selected body '+name,hashlib.sha256(B.R.read(cap,name)).hexdigest()==h)
for role,ref in exp['inputs'].items():ok('actual eight role '+role,hashlib.sha256(B.R.read(cap,ref['path'])).hexdigest()==ref['sha256']==q['input_hashes'][role])
ok('eight input denominator',len(q['input_hashes'])==8)
# Extract only pure census predicates; never execute verify() against absent future outcomes.
nodes=[n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name in ('final_cpu_census','early_cpu_evidence')];ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual bound CPU predicates>','exec'),ns)
for value in ({},{'11':[3]},{'11':[7]},{'11':[3,7]}):ok('accepted empty/subset census '+repr(value),ns['final_cpu_census']([3,7],value))
for value in (None,[],{'11':[]},{'11':[8]},{'11':[True]},{'11':[7,3]},{'11':[3,3]}):ok('invalid census refused '+repr(value),not ns['final_cpu_census']([3,7],value))
for guard,ready,release in ((None,None,None),({},None,None),({}, {}, {})):ok('absent actual early evidence remains refused '+repr((guard,ready,release)),not ns['early_cpu_evidence'](guard,ready,release))
refuse('old request not rebound',lambda:B.authenticate(request,B.OLD_QHASH));ok('zero authority actualbinding',constructed['binding']['outcome_classified'] is False and constructed['binding']['numerical_authority'] is False);ok('no numerical modules',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
(D/'ACTUAL_JOINS01.json').write_text(json.dumps({'request_sha256':pin,'current_source_head':head,'current_source_pins':324,'input_count':8,'actual_proofs':proofrows,'original_generator_tool':'b4d2cb','original_manifest_failure_tool':'efec9c','actual_emitter_reexecuted':False,'outcome_verifier_executed':False,'claim_census_observed':None,'fresh_native_eligibility':None,'complete_final_union_recovery':None},sort_keys=True,indent=2)+'\n');(D/'CHECKS01.json').write_text(json.dumps({'verdict':'ACCEPTED_EXACT_ACTUAL_VERIFIER_BINDING_SOURCE_ONLY','count':len(checks),'checks':checks,'outcome_verifier_executed':False,'actual_admission_calls':0,'actual_claim_reads':0,'native_executions':0,'network_operations':0,'actual_emitter_reexecuted':False,'numerical_authority':None},sort_keys=True,indent=2)+'\n');print(json.dumps({'verdict':'ACCEPTED_EXACT_ACTUAL_VERIFIER_BINDING_SOURCE_ONLY','count':len(checks)}))
