"""Real read-only Admission and source bodies; no Run/Owner/Binding/numerical import."""
import ast,copy,hashlib,json,os,resource,subprocess,sys,types,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(60,60));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
sys.path.insert(0,str(ROOT))
from tradingagents.research.admission import admit,Admission
from tradingagents.research.onchain_replication import job,matching_pair
from tradingagents.research.onchain_replication.provenance import digest,file_hash
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();gate=str((H.parent/'real-data-pilot-full24-entry01-2026-10-09/gate01.json').relative_to(ROOT));name='eth-paper-real-data-end-to-end-resource-20261009-24'
ad=admit(root=ROOT,registration=gate,experiment=name,source=source,_own_claim=name)
assert type(ad) is Admission
policy=json.loads((ROOT/ad.inputs['pair_policy']['path']).read_text());numerical=policy['numerical_source'];required=job.required_sources()
old=(S/'matching_owner.py').read_text();new=(H/'matching_owner.py').read_text();tree=ast.parse(new)
def require(v,m):
 if not v:raise ValueError(m)
ns=dict(ROOT=ROOT,SELF='tradingagents/research/onchain_replication/matching_owner.py',job=job,matching_pair=matching_pair,file_hash=file_hash,digest=digest,subprocess=subprocess,require=require)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_anchor_blobs','_anchor_read','validate_numerical_source')],type_ignores=[]),'<actual candidate validator AST>','exec'),ns)
check=ns['validate_numerical_source'];refusals={}
def refuses(label,value):
 try:check(ad,value)
 except (ValueError,subprocess.CalledProcessError) as error:refusals[label]=str(error)
 else:raise AssertionError(label)
refuses('original181',numerical)
correct={'commit':numerical['commit'],'files':{n:ad.experiment['source_files'][n] for n in sorted(required)}}
check(ad,correct)
x=copy.deepcopy(correct);x['files']['not-a-member.py']='0'*64;refuses('nonmember',x)
x=copy.deepcopy(correct);x['files'][sorted(required)[0]]='0'*64;refuses('wrong_pin',x)
x=copy.deepcopy(correct);x['commit']='0'*40;refuses('wrong_anchor',x)
# Exact original validator statement body after extraction, no checks removed/reordered.
a=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='_source')
b=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_numerical_source')
assert ast.dump(ast.Module(body=a.body[1:],type_ignores=[]))==ast.dump(ast.Module(body=b.body,type_ignores=[]))
# Original first line contains3 assignments: remove only ad=run.admission.
# AST body[1:] still includes registered/required assignments because semicolons parse separately.
caller=(H/'real_pilot_import_caller.py').read_text();insertion="    from .matching_owner import validate_numerical_source\n    validate_numerical_source(ad,_read(ad,s['pair_checkpoint_input'])['numerical_source'])\n"
assert caller.replace(insertion,'',1)==(S/'real_pilot_import_caller.py').read_text()
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
for filename in ('matching_owner.py','real_pilot_import_caller.py'):
 (H/(filename+'.inverse.patch')).write_text(''.join(difflib.unified_diff((H/filename).read_text().splitlines(True),(S/filename).read_text().splitlines(True),fromfile='candidate/'+filename,tofile='original/'+filename)))
r=dict(status='PASS_METADATA_SOURCE_ONLY',source=source,actual_admission=True,own_claim_readonly_revalidation=name,required=len(required),original=len(numerical['files']),missing=sorted(required-set(numerical['files'])),anchor=correct['commit'],all193_current_bodies_match_anchor=True,refusals=refusals,no_numpy_torch=True,body_order_inverse=True,caller_literal_inverse=True,graph_data_read=False,empirical_execution=False)
(H/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
