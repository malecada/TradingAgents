"""Narrow identity/source-anchor and exact input-byte composition review."""
from pathlib import Path
import ast,copy,hashlib,json,os,stat,subprocess,sys,types
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
FS=HERE.parent.parent
D=FS/'real-data-pilot-final02-2026-10-06'
NAME='eth-paper-real-data-end-to-end-resource-20261006-02'
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
previous=json.loads((HERE.parent/'successor02/RELEASE_REVIEW01.json').read_bytes())
evidence=previous['evidence'].copy()
oldprivate='research_artifacts/real_pilot_runtime/pilot-transport-20261006-02/archive_transport01.json'
assert oldprivate in evidence;del evidence[oldprivate]
def body(p):
    assert p.stat().st_size<=4*1024**2 and 'real_pilot_runtime' not in p.parts and p.name!='connection.json'
    b=p.read_bytes();evidence[str(p.relative_to(ROOT))]=sha(b);return b
def read(p):return json.loads(body(p))
def auth(r):
    b=body(ROOT/r['path']);assert sha(b)==r['sha256'];return json.loads(b)
def need(v,m):
    if not v:raise ValueError(m)
oldgate=read(D/'PREDECESSOR_gate01.json');gate=read(D/'gate01.json')
x=oldgate['experiments'][NAME];y=gate['experiments'][NAME]
assert {k for k in x if x[k]!=y[k]}=={'inputs','source_files'}
for k in ('datasets','families','program_id','schema_version'):assert oldgate[k]==gate[k]
changed={p for p in x['source_files'] if x['source_files'][p]!=y['source_files'][p]}
source_path='tradingagents/research/onchain_replication/real_pilot_storage.py'
assert changed=={source_path} and set(x['source_files'])==set(y['source_files']) and len(y['source_files'])==201
candidate=read(HERE.parent/'native-identity02/REVIEW01.json');assert candidate['decision']=='accepted'
assert sha(body(ROOT/source_path))==y['source_files'][source_path]==candidate['candidate_sha256']
for p,h in y['source_files'].items():
    if p!=source_path:assert previous['evidence'][p]==h
    evidence[p]=h
reanchor=read(D/'NUMERICAL_CONTEXT_REANCHOR01.json')
oldpair=auth(reanchor['old_pair_policy']);pair=auth(reanchor['new_pair_policy'])
expected=copy.deepcopy(oldpair);expected['numerical_source']['commit']=reanchor['source_commit'];expected['numerical_source']['files'][source_path]=candidate['candidate_sha256'];assert expected==pair
assert len(pair['numerical_source']['files'])==178
git_changed=subprocess.check_output(['git','diff','--name-only',oldpair['numerical_source']['commit'],pair['numerical_source']['commit'],'--','tradingagents'],cwd=ROOT,text=True).splitlines()
assert git_changed==[source_path]
committed=subprocess.check_output(['git','show',pair['numerical_source']['commit']+':'+source_path],cwd=ROOT)
assert sha(committed)==candidate['candidate_sha256']
binding=read(D/'BINDING_DRAFT05.json');draft=auth(binding['draft']);saved=auth(binding['preparation']);bound=auth(binding['transport_binding'])
oldbinding=read(D/'PREDECESSOR_BINDING01.json')
for k in ('baseline','prior_outcome_review','prior_preservation_complete','prior_recovery_review'):assert binding[k]==oldbinding[k]
assert bound['source_request']['prepared']==binding['preparation']
preflight=body(D/'preflight01.py');assert sha(preflight)==previous['preflight_sha256']
su=FS/'real-data-pilot-packed-feature-successor03-2026-10-06/successor02.py'
assert sha(body(su))==previous['evidence'][str(su.relative_to(ROOT))]
m=types.ModuleType('reanchor_prepare');m.__file__=str(su);exec(compile(body(su),str(su),'exec'),vars(m))
assert m.prepare(ROOT,draft)==saved
tree=ast.parse(preflight);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding')
env={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact pure inverse>','exec'),env)
archive=auth(saved['builder03_spec']['references'][saved['builder03_spec']['template_roles']['archive']])
env['inverse_binding'](saved,archive,bound,binding['transport'],raw,sha)
docs={}
for role,value in bound['inputs'].items():
    ref=y['inputs'][role];b=body(ROOT/ref['path']);assert sha(b)==ref['sha256'] and b==raw(value)
    docs[role]=json.loads(b);expected=auth(x['inputs'][role])
    if role in ('execution_job','producer_plan'):
        descriptor=expected['payload']['representation_jobs']['original32']['descriptor'] if role=='execution_job' else expected['producers']['original32']['descriptor']
        descriptor['pair_execution']['policy_sha256']=y['inputs']['pair_policy']['sha256']
    assert docs[role]==expected,role
private=binding['transport'];assert all(y['inputs']['archive_transport'][k]==private[k] for k in ('path','sha256'))
assert private['sha256']==oldbinding['transport']['sha256'] and private['path']!=oldbinding['transport']['path']
path=ROOT/private['path'];s=path.lstat();p=path.parent.lstat()
assert path.resolve()==path and s.st_nlink==1 and s.st_size==private['bytes'] and s.st_uid==p.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600 and stat.S_IMODE(p.st_mode)==0o700
evidence[private['path']]=private['sha256']
for role,ref in y['inputs'].items():
    if role in docs or role=='archive_transport':continue
    if role=='pair_policy':assert sha(body(ROOT/ref['path']))==ref['sha256'];continue
    assert ref==x['inputs'][role] and previous['evidence'][ref['path']]==ref['sha256'];evidence[ref['path']]=ref['sha256']
selection=docs['execution_job']['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32']
assert selection['descriptor']==producer['descriptor']
for field,key,hkey in [('compact_policy_input','compact_execution','policy_sha256'),('compact_archive_input','compact_archive_execution','policy_sha256'),('pair_checkpoint_input','pair_execution','policy_sha256'),('original_dictionary_input','original_dictionary_import','sha256'),('original_dictionary_stage_input','original_dictionary_stage','sha256')]:
    role=selection[field];assert role==producer[field] and selection['descriptor'][key][hkey]==y['inputs'][role]['sha256']
for field in ('compact_mcm_input','compact_mcm_output_input'):assert selection[field]==producer[field] and selection[field] in y['inputs']
assert docs['pilot']['resource_policy']==docs['execution_job']['resources']
assert all(evidence[p]==h for p,h in y['source_files'].items()) and all(evidence[v['path']]==v['sha256'] for v in y['inputs'].values())
admission=read(D/'ACTUAL_READONLY_ADMISSION02.json');assert admission['ready'] and admission['effective_attempt_budget']==73 and admission['source_pins']==201 and admission['input_roles']==59
assert sha(subprocess.check_output(['git','show',admission['source']+':'+str((D/'gate01.json').relative_to(ROOT))],cwd=ROOT))==sha(body(D/'PREDECESSOR_gate02.json'))
assert not (ROOT/'research_runs'/NAME).exists() and not any(k in sys.modules for k in ('numpy','torch','scipy','tradingagents'))
findings=[]
badgate=read(D/'PREDECESSOR_gate02.json');badexp=badgate['experiments'][NAME]
for role,key,hkey in [('archive_policy','compact_archive_execution','policy_sha256'),('original_import','original_dictionary_import','sha256')]:
    ref=badexp['inputs'][role];b=body(ROOT/ref['path']);assert sha(b)==ref['sha256'] and ref['sha256']!=selection['descriptor'][key][hkey] and sha(raw(json.loads(b)))==selection['descriptor'][key][hkey]
    findings.append({'severity':'P1','status':'resolved_inputs03','file':ref['path'],'line':1,'problem':'Pretty serialization changed admitted hash; both descriptors retained canonical hash.','impact':'Later archive/import exact descriptor validation would fail although _admitted passed.','resolution':'Preserved inputs02/gate02/admission02; current inputs03 are exact binder.raw bytes, all five descriptor joins now pass.'})
read(D/'SERIALIZATION_CORRECTION01.json')
result={'schema_version':1,'status':'PASS_NARROW_REANCHOR_AND_EXACT_BYTES','identity':NAME,'changed_source_pins':[source_path],'git_only_changed_package_body':[source_path],'source_anchor':pair['numerical_source']['commit'],'package_pins':178,'source_pins':201,'input_roles':59,'pure_prepare_equal':True,'binder_inverse_equal':True,'generated_whole_doc_transform':'Only both pair_execution SHA fields; every other value unchanged. Exact canonical serialized bytes checked.','descriptor_joins':True,'genuine_root_admission02':admission,'private_body_read':False,'findings':findings,'evidence':evidence}
(HERE/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
six={binding[k]['path']:binding[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding')}
review={'schema_version':1,'decision':'accepted','identity':NAME,'reviewer':'independent pilot_correction_review','scope':'Current exact six-reference composition after accepted one-literal control source reanchor and canonical input serialization correction. Source178 one control pin only; no science/resources/budget changes. Final binding/release and actual current committed admission/fresh entry remain mandatory.','evidence':six,'findings':findings,'checks':{'package_pins':178,'source_pins':201,'input_roles':59,'pure_prepare_equal':True,'binder_inverse_equal':True,'all_descriptor_joins':True,'exact_canonical_generated_bytes':True},'private_input_qualification':'Same public binder digest, fresh protected path stat checked. Private body never opened; mandatory opaque entry hash remains.'}
(HERE/'BINDING_REVIEW01.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print('BINDING_REVIEW01',sha((HERE/'BINDING_REVIEW01.json').read_bytes()))
print('CHECK01',sha((HERE/'CHECK01.json').read_bytes()))
