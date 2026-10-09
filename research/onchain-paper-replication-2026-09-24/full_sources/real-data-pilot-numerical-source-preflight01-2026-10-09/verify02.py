"""Read-only closed Admission; actual source metadata, no Run or numerical imports."""
import ast,copy,hashlib,json,os,resource,subprocess,sys,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(60,60));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
# Process-local Git mapping bounds, no repository config writes.
os.environ.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.packedGitWindowSize',GIT_CONFIG_VALUE_0='1m',GIT_CONFIG_KEY_1='core.packedGitLimit',GIT_CONFIG_VALUE_1='16m')
sys.path.insert(0,str(ROOT))
from tradingagents.research.admission import admit,Admission
from tradingagents.research.onchain_replication import job,matching_pair
from tradingagents.research.onchain_replication.provenance import digest,file_hash
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();gate=str((H.parent/'real-data-pilot-full24-entry01-2026-10-09/gate01.json').relative_to(ROOT));name='eth-paper-real-data-end-to-end-resource-20261009-24'
ad=admit(root=ROOT,registration=gate,experiment=name,source=source,_own_claim=name)
assert type(ad) is Admission
policy=json.loads((ROOT/ad.inputs['pair_policy']['path']).read_text());numerical=policy['numerical_source'];required=job.required_sources()
new=(H/'real_pilot_import_caller02.py').read_text();old=(S/'real_pilot_import_caller.py').read_text()
start=new.index('    from .job import required_sources\n',new.index('def admitted('));end=new.index('    p = config',start)
insert=new[start:end];assert new[:start]+new[end:]==old
statements=ast.parse(insert.replace('    ','',1) if False else __import__('textwrap').dedent(insert)).body
# Execute the exact three predicate statements; metadata is supplied directly from genuine Admission.
predicates=statements[3:]
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns=dict(ad=ad,required_sources=job.required_sources,hash_string=matching_pair.hash_string,require=require)
code=compile(ast.Module(body=predicates,type_ignores=[]),'<actual early predicates>','exec')
def check(value):ns['numerical']=value;exec(code,ns)
refusals={}
def refuses(label,value):
 try:check(value)
 except (ValueError,TypeError) as e:refusals[label]=str(e)
 else:raise AssertionError(label)
refuses('original181',numerical)
correct={'commit':numerical['commit'],'files':{p:ad.experiment['source_files'][p] for p in sorted(required)}};check(correct)
for label,change in [('nonmember',lambda x:x['files'].update({'not-a-member.py':'0'*64})),('wrong_pin',lambda x:x['files'].update({sorted(required)[0]:'0'*64})),('malformed_anchor',lambda x:x.update(commit='bad')),('extra_field',lambda x:x.update(extra=1)),('wrong_files_type',lambda x:x.update(files=[]))]:
 x=copy.deepcopy(correct);change(x);refuses(label,x)
# Original unchanged runtime anchor reader, source bodies only.
owner=(S/'matching_owner.py').read_text();tree=ast.parse(owner)
anchor_ns=dict(subprocess=subprocess,require=require)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_anchor_blobs','_anchor_read')],type_ignores=[]),'<original anchor readers>','exec'),anchor_ns)
names=sorted(required);sizes=[(ROOT/p).stat().st_size for p in names]
bodies=anchor_ns['_anchor_read'](ROOT,correct['commit'],names,sizes)
for p,raw in zip(names,bodies,strict=True):assert digest(raw)==correct['files'][p]==file_hash(ROOT/p)
try:anchor_ns['_anchor_read'](ROOT,'0'*40,names,sizes)
except (ValueError,subprocess.CalledProcessError) as e:refusals['runtime_wrong_anchor']=str(e)
else:raise AssertionError('bad anchor')
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
(H/'caller02.inverse.patch').write_text(''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile='candidate/caller',tofile='original/caller')))
r=dict(status='PASS_METADATA_SOURCE_ONLY',source=source,actual_admission=True,own_claim_readonly_revalidation=name,required=len(required),original=len(numerical['files']),missing=sorted(required-set(numerical['files'])),anchor=correct['commit'],all193_current_bodies_match_anchor=True,refusals=refusals,no_numpy_torch=True,caller_literal_inverse=True,graph_data_read=False,empirical_execution=False)
(H/'RESULT02.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
