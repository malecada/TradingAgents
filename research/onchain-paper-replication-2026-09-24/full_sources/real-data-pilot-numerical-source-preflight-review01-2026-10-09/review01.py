import ast,copy,hashlib,json,os,pathlib,resource,signal,subprocess,sys,textwrap
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.environ.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.packedGitWindowSize',GIT_CONFIG_VALUE_0='1m',GIT_CONFIG_KEY_1='core.packedGitLimit',GIT_CONFIG_VALUE_1='16m',GIT_NO_LAZY_FETCH='1')
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();C=F/'real-data-pilot-numerical-source-preflight01-2026-10-09';S=ROOT/'tradingagents/research/onchain_replication';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=lambda p:json.loads(p.read_bytes())
m=j(C/'MANIFEST01.json');assert h(C/'real_pilot_import_caller02.py')=='4bbcbe7c698ff8eb94fdaf9c9bdbad66fcb5a6af48898c87bdcc752fc5d28269'
for p,v in m['evidence'].items():assert h(C/p)==v
assert h(S/'matching_owner.py')==m['unchanged_runtime_owner_sha256']
new=(C/'real_pilot_import_caller02.py').read_text();old=(S/'real_pilot_import_caller.py').read_text();start=new.index('    from .job import required_sources\n',new.index('def admitted('));end=new.index('    p = validate_plan',start);assert new[:start]+new[end:]==old
insert=ast.parse(textwrap.dedent(new[start:end]));assert len(insert.body)==6 and isinstance(insert.body[2],ast.Assign)
# Genuine closed24 read-only Admission, never Run/Owner/start; numerical modules not imported.
sys.path.insert(0,str(ROOT))
from tradingagents.research.admission import admit,Admission
from tradingagents.research.onchain_replication import job,matching_pair
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();name='eth-paper-real-data-end-to-end-resource-20261009-24';ad=admit(root=ROOT,registration=str((F/'real-data-pilot-full24-entry01-2026-10-09/gate01.json').relative_to(ROOT)),experiment=name,source=head,_own_claim=name);assert type(ad) is Admission
numerical=j(ROOT/ad.inputs['pair_policy']['path'])['numerical_source'];required=job.required_sources();assert len(required)==193 and len(numerical['files'])==181
correct={'commit':numerical['commit'],'files':{p:ad.experiment['source_files'][p] for p in sorted(required)}}
def require(ok,message):
 if not ok:raise ValueError(message)
scope={'ad':ad,'required_sources':job.required_sources,'hash_string':matching_pair.hash_string,'require':require};code=compile(ast.Module(body=insert.body[3:],type_ignores=[]),'<exact candidate predicates>','exec')
def check(x):scope['numerical']=x;exec(code,scope)
check(correct);failures={}
values={'original181':numerical,'wrong_type':[],'files_wrong_type':dict(correct,files=[]),'extra_field':dict(correct,unexpected=True),'bad_hex':dict(correct,commit='g'*40),'uppercase_hex':dict(correct,commit='A'*40),'integer_anchor':dict(correct,commit=5)}
x=copy.deepcopy(correct);x['files'].pop(next(iter(x['files'])));values['missing_member']=x
x=copy.deepcopy(correct);x['files']['extra.py']='0'*64;values['extra_member']=x
x=copy.deepcopy(correct);x['files'][next(iter(x['files']))]='0'*64;values['wrong_pin']=x
for k,v in values.items():
 try:check(v)
 except (ValueError,TypeError) as e:failures[k]=str(e)
 else:raise AssertionError(k)
# A well-formed unavailable anchor deliberately passes early syntax; original runtime reader still rejects.
check(dict(correct,commit='0'*40))
owner_tree=ast.parse((S/'matching_owner.py').read_bytes());anchor_scope={'subprocess':subprocess,'require':require,'matching_pair':matching_pair}
exec(compile(ast.Module(body=[n for n in owner_tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_anchor_blobs','_anchor_read')],type_ignores=[]),'<unchanged anchor readers>','exec'),anchor_scope)
paths=sorted(required);sizes=[(ROOT/p).stat().st_size for p in paths]
for p,body in zip(paths,anchor_scope['_anchor_read'](ROOT,correct['commit'],paths,sizes),strict=True):assert hashlib.sha256(body).hexdigest()==correct['files'][p]==h(ROOT/p)
try:list(anchor_scope['_anchor_read'](ROOT,'0'*40,paths,sizes))
except (ValueError,subprocess.CalledProcessError) as e:failures['runtime_unavailable_anchor']=str(e)
else:raise AssertionError('runtime anchor')
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
r={'decision':'accepted_source_only','selected_source':{'path':str((C/'real_pilot_import_caller02.py').relative_to(ROOT)),'sha256':h(C/'real_pilot_import_caller02.py'),'install_as':'tradingagents/research/onchain_replication/real_pilot_import_caller.py','baseline_sha256':h(S/'real_pilot_import_caller.py')},'manifest_sha256':h(C/'MANIFEST01.json'),'runtime_owner_unchanged_sha256':h(S/'matching_owner.py'),'checks':{'genuine_closed24_admission':True,'read_only_admission_source':head,'original181_refused':True,'complete193_metadata_passed':True,'literal_full_inverse':True,'original_runtime193_anchor_bodies_joined':True,'original_anchor':correct['commit'],'refusals':failures,'no_numpy_torch':True},'qualification':'Six inserted early metadata lines only. Existing policy read authenticates metadata; current source roster/pins and commit syntax are checked before pilot resource binding/graph work. Well-formed missing anchors intentionally pass early syntax; original Owner local-body/Git-anchor and all numerical/resource/runtime checks remain byte-identical. No candidate full caller, Run, Owner, claim, graph arrays, network, native job or empirical authority exercised. Only caller02 selected; other candidate drafts excluded. No performance claim.'}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'sha256':h(R/'SOURCE_REVIEW01.json'),'refusal_count':len(failures)}))
