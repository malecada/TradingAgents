"""Independent stdlib/source review; no Run, owner, graph arrays or cohort fabricated."""
import ast,copy,dataclasses,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'paper-treatment-production-preparation01-2026-10-04';O=C/'overlay/tradingagents/research/onchain_replication'
checks=[];witnesses=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def body(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2;return p.read_bytes()
ok('candidate MANIFEST02 exact',sha(body(C/'MANIFEST02.json'))=='b3f23d2d304acb31c2fb75dfe830f31d0cfb3abef6861ec747aafaa21146b6ec')
manifest=json.loads(body(C/'MANIFEST02.json'));rows=manifest['entries'];actual={p.relative_to(C).as_posix() for p in C.rglob('*')}
ok('complete typed candidate paths',len({r['path'] for r in rows})==len(rows) and actual=={r['path'] for r in rows}|{'MANIFEST02.json'})
for r in rows:
 p=C/r['path'];s=p.lstat();ok('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['type']=='file':ok('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(body(p))==r['sha256'])
 else:ok('directory '+r['path'],r['type']=='directory' and stat.S_ISDIR(s.st_mode))
for r in json.loads(body(C/'ORIGINS01.json')):ok('actual unchanged original '+r['snapshot'],body(Path(r['path']))==body(C/r['snapshot']) and sha(body(C/r['snapshot']))==r['sha256'])
base=body(C/'baseline-job.py');new=body(O/'job.py');inv=json.loads(body(C/'JOB_INVERSE01.json'));restored=new
for change in reversed(inv['changes']):
 old=change['old'].encode();text=change['new'].encode();ok('one declared job substitution '+change['old'][:40],restored.count(text)==1);restored=restored.replace(text,old,1)
ok('four substitutions only and full byte inverse',len(inv['changes'])==4 and restored==base and sha(base)==inv['baseline_sha256'])
ok('whole job AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(base)))
actualjob=Path('tradingagents/research/onchain_replication/job.py');ok('actual Main job baseline unchanged',body(actualjob)==base)
actualpackage=actualjob.parent;closure={str(p) for p in actualpackage.glob('*.py')}|{str(p) for p in actualpackage.parent.glob('*.py')}|{'tradingagents/__init__.py'}
ok('actual135/prospective137 source closure',len(closure)==135 and len(closure|{str(actualpackage/'treatment_contract.py'),str(actualpackage/'treatment_production.py')})==137)
spec=importlib.util.spec_from_file_location('opaque_treatment_contract',O/'treatment_contract.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
weeks=['2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-17T00:00:00Z']
ref={'manifest_input':'opaque_manifest','coverage_input':'opaque_coverage','claim_input':'opaque_claim_role','terminal_input':'opaque_terminal_role','ledger_input':'opaque_ledger_role','components':{'edge_index.npy':'opaque_component_role'}}
plan={'schema_version':1,'kind':'paper-graph-treatment-v1','asset':'ETH','variant':'whale','coverage':[[weeks[0],'2022-01-24T00:00:00Z']],'expected_weeks':weeks,'parents':{w:copy.deepcopy(ref) for w in weeks},'cohort_input':None,'cohort_review_input':None}
ok('exact three-week denominator',contract.schema(plan)==['treatment-eth-whale-'+w[:10] for w in weeks])
def refuses(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):checks.append(n);return
 raise AssertionError(n)
mutations={'missing_week':lambda p:p['expected_weeks'].pop(),'missing_parent':lambda p:p['parents'].pop(weeks[0]),'extra_parent':lambda p:p['parents'].update({'2022-01-24T00:00:00Z':ref}),'duplicate_coverage':lambda p:p['coverage'].append(p['coverage'][0]),'unsorted_weeks':lambda p:p['expected_weeks'].reverse(),'partial_week':lambda p:p['coverage'][0].__setitem__(1,'2022-01-23T00:00:00Z'),'extra_field':lambda p:p.update(opaque=True),'boolean_version':lambda p:p.update(schema_version=True),'bad_asset':lambda p:p.update(asset='OTHER'),'bad_variant':lambda p:p.update(variant='latest_cohort'),'absolute_role':lambda p:p['parents'][weeks[0]].update(manifest_input='/opaque'),'traversing_component':lambda p:p['parents'][weeks[0]]['components'].update({'../opaque.npy':'opaque_role'}),'unpaired_cohort':lambda p:p.update(variant='fund',cohort_input='opaque_cohort')}
for name,mutate in mutations.items():
 p=copy.deepcopy(plan);mutate(p);refuses('plan refuses '+name,lambda p=p:contract.schema(p))
p=copy.deepcopy(plan);p['variant']='fund';ok('missing fund cohort retains all declared cells',len(contract.schema(p))==3);p['asset']='BTC';refuses('BTC fund refused',lambda:contract.schema(p))
refuses('empty cohort evidence refused',lambda:contract.cohort({}, {},'0'*64,weeks[0],weeks[1]))
refuses('absent parent metadata refused',lambda:contract.parent_receipts({}, {}, [],'0'*64,'1'*64,weeks[0],'ETH'))
production=body(O/'treatment_production.py').decode();tree=ast.parse(production);producer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='produce_registered_treatments');guard=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_guard')
ok('guard first operation',ast.unparse(producer.body[0])=='_guard(run, plan_input)')
ok('guard exact ResearchRun type and active/source checks',"type(run)is ResearchRun" in ast.get_source_segment(production,guard) and 'run._active();run._check_source()' in production)
ok('missing cohort before numerical imports',production.index("p['cohort_input'] is None")<production.index('from .graph_store import'))
ok('full terminal claim ledger coverage source predicates present',all(s in production for s in ["terminal.get('source')==claim.get('source')","terminal.get('registration_sha256')==claim.get('registration_sha256')","terminal.get('output_sha256',{}).get('cell-ledger.json')==digest(lraw)","terminal.get('cells')==ledger","proof.get('claim_sha256')==digest(craw)","parent_row.get('coverage_sha256')==digest(praw)"]))
ok('exact original treatment functions selected',"(filter_graph if p['asset']=='ETH' else filter_btc_graph)(value,p['variant'],cohort=members,cohort_hash=cohort_hash)" in production)
# Scalar-only exact availability branch, with no addresses or GraphSnapshot.
@dataclasses.dataclass(frozen=True)
class OpaqueTime:
 available_at:str
branch=next(n for n in ast.walk(producer) if isinstance(n,ast.If) and 'cohort_doc is not None and' in ast.unparse(n.test))
for graph_time,known in [('2022-01-11T00:00:00Z','2022-01-01T00:00:00Z'),('2022-01-11T00:00:00Z','2022-01-11T00:00:00Z'),('2022-01-11T00:00:00Z','2026-01-01T00:00:00Z')]:
 env={'cohort_doc':{'known_at':known},'graph':OpaqueTime(graph_time),'stamp':contract.stamp};env['transformed']=env['graph'];exec(compile(ast.Module(body=[branch],type_ignores=[]),'exact-availability','exec'),env)
 ok('availability max '+known,contract.stamp(env['graph'].available_at)==max(contract.stamp(graph_time),contract.stamp(known)))
# T1 exact producer/reconciler namespace witness; no authority object constructed.
dir_assign=next(n for n in producer.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='directory' for t in n.targets))
jobtree=ast.parse(new);reconcile=next(n for n in jobtree.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile')
observer_loop=next(n for n in ast.walk(reconcile) if isinstance(n,ast.For) and "claim['experiment']['cells']"==ast.unparse(n.iter))
path_assign=next(n for n in observer_loop.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='path' for t in n.targets))
producer_constants=[n.value for n in ast.walk(dir_assign.value) if isinstance(n,ast.Constant) and isinstance(n.value,str)];observer_constants=[n.value for n in ast.walk(path_assign.value) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
ok('T1 producer uses treatments namespace',any(s.endswith('/treatments') for s in producer_constants))
ok('T1 observer scans only sources namespace','sources' in observer_constants and 'treatments' not in ast.get_source_segment(new.decode(),reconcile))
# Derive exact path suffixes from source constants for a bounded opaque filename.
prefix=next(s for s in producer_constants if s.endswith('/treatments'));produced=Path('/opaque-root')/prefix/'opaque-id'/'opaque-cell.json';observed=Path('/opaque-root')/'research_artifacts/onchain-paper-replication-2026-09-24'/'sources'/'opaque-id'/'opaque-cell.json'
ok('T1 durable treatment and scanned row cannot coincide',produced!=observed)
witnesses.append({'id':'T1','producer_line':dir_assign.lineno,'producer_segment':ast.get_source_segment(production,dir_assign),'observer_line':path_assign.lineno,'observer_segment':ast.get_source_segment(new.decode(),path_assign),'opaque_produced_path':str(produced),'opaque_observed_path':str(observed),'actual_Run_or_claim_constructed':False,'impact':'After later failure, actual durable treatment rows are not read by unchanged reconciliation; it synthesizes unavailable dispositions instead.'})
# T2 exact pending loop and first-fatal reducer, using scalar callbacks only.
pending=next(n for n in ast.walk(producer) if isinstance(n,ast.FunctionDef) and n.name=='pending');close=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_close')
primary=KeyboardInterrupt('opaque original fatal');attempts=[];recorded={};summary_attempt=[];ids=['opaque-a','opaque-b','opaque-c']
def record(row):
 attempts.append(row['id'])
 if row['id']=='opaque-a':raise OSError('opaque first row publication failure')
 recorded[row['id']]=row
env={'p':{'expected_weeks':weeks},'ids':ids,'rows':recorded,'record':record,'primary':primary};exec(compile(ast.Module(body=[pending,close],type_ignores=[]),'exact-pending-and-finalizer','exec'),env)
error=None
try:env['_close']((env['pending'],lambda:summary_attempt.append(True)),primary)
except BaseException as e:error=e
ok('first actual fatal preserved',error is primary)
ok('T2 later per-week finalization not attempted',attempts==['opaque-a'] and not recorded and summary_attempt==[True])
witnesses.append({'id':'T2','line':pending.lineno,'segment':ast.get_source_segment(production,pending),'declared_ids':ids,'attempted_record_ids':attempts,'retained_row_ids':list(recorded),'summary_action_attempted':summary_attempt==[True],'original_fatal_preserved':error is primary,'actual_file_or_claim_publication':False,'impact':'One unavailable-row writer failure prevents attempts for all subsequent pending cells; later summary depends on missing rows.'})
population=body(C/'origins/population_assembly.py').decode();ok('mandatory downstream treatment receipt contract absent','treatment_receipt' not in population and 'treatment.json' not in population)
ok('producer explicitly withholds downstream authority','explicit treatment-receipt admission and common-mask population still required' in production)
ok('no numerical or genuine research modules imported',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')) and not any(n.startswith('tradingagents') for n in sys.modules))
out={'schema_version':1,'checks':checks,'count':len(checks),'candidate_members':len(rows),'candidate_regular_files':sum(r['type']=='file' for r in rows),'candidate_source_pins':{n:sha(body(O/n)) for n in ('job.py','treatment_contract.py','treatment_production.py')},'findings':witnesses,'actual_Run_or_claim_constructed':False,'actual_native_execution':False,'numerical_imports':False,'array_or_sample_decode':False,'fund_address_cohort_created':False,'downstream_fit_admission':'WITHHELD_MANDATORY_RECEIPT_CONTRACT_MISSING','future_source':None,'future_registration':None,'financial_credit':0}
(H/'CHECKS02.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(len(checks),'independent treatment checks passed; T1/T2 witnesses retained')
