import ast, copy, hashlib, json, types
from pathlib import Path
ROOT=Path.cwd(); F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
HERE=Path(__file__).resolve().parent
NEW=F/'real-data-pilot-fixed20-metadata-successor01-2026-10-08'
OLD=F/'real-data-pilot-fixed19-metadata-successor01-2026-10-08'
SEL=F/'real-data-pilot-capacity-selection03-2026-10-08'
sources={}; checks=[]
def pin(p, expected=None):
    b=p.read_bytes(); h=hashlib.sha256(b).hexdigest(); sources[str(p.relative_to(ROOT))]=h
    assert expected is None or h==expected,(str(p),h)
    return b

def check(name, ok):
    assert ok,name
    checks.append(name)

new=pin(NEW/'candidate/residuals03.py','082ca101c0ac68786e8d05b4eb012d4a8db125af9c81ab9e97ec0719f1656160').decode()
old=pin(NEW/'candidate/original_residuals02.py').decode()
pin(F/'real-data-pilot-capacity-budget-review01-2026-10-08/MANIFEST02.json','d7085c489088a3904f460f1464434bd7612a3b6e4f8e40f9e70b50a6f907840e')
selection=json.loads(pin(SEL/'CONTROL_SELECTION01.json','1d34ff8c337877948a941d6a7fad518171c734ec64643c258535f21edaf504c2'))
for v in selection['policies'].values(): pin(ROOT/v['path'],v['sha256'])
start=new.index('    # Preserve the legacy inventory.')
end=new.index('    checkpoint_dirs=',start)
inverse=new[:start]+'    checkpoint_files=7*(10*G+9*S+51)\n'+new[end:]
inverse=inverse.replace('max(M,K,p[\'max_input_bytes\']),2*K,scratch_files,K,basis=', 'max(M,K,p[\'max_input_bytes\']),2*K,8,K,basis=')
check('exact_source_inverse',inverse==old)
check('exact_ast_inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)))
check('loader_byte_identical',pin(NEW/'successor02.py')==pin(OLD/'successor02.py'))
a=json.loads(pin(NEW/'DEPENDENCIES02.json')); b=json.loads(pin(OLD/'DEPENDENCIES02.json'))
check('only_residual_pin_changed',[k for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)]==['residuals'])
check('old_residual_is_pinned_predecessor',pin(ROOT/b['residuals']['path'],b['residuals']['sha256']).decode()==old)
check('new_residual_pin_exact',a['residuals']['sha256']==sources[str((NEW/'candidate/residuals03.py').relative_to(ROOT))])
check('storage_helper_exact_main',pin(NEW/'candidate/real_pilot_storage.py')==pin(ROOT/'tradingagents/research/onchain_replication/real_pilot_storage.py'))
def load(src,path):
    m=types.ModuleType('bounded'); m.__file__=str(path); exec(compile(src,str(path),'exec'),m.__dict__); return m
n=load(new,NEW/'candidate/residuals03.py'); o=load(old,NEW/'candidate/original_residuals02.py')
stage=json.loads((SEL/'compact_policy.json').read_text())['stage_policy']
kwargs=dict(native_file_bytes=selection['checkpoint_native_file_bytes'],training_checkpoint_bytes=4*1024**2,runtime_reservation=dict(logical_bytes=1024**2,regular_files=16,directories=13,max_file_bytes=1024**2))
def normalized(v):
    v=copy.deepcopy(v)
    for d in v['residual_domains'].values(): d.pop('evidence_sha256')
    return v
legacy=copy.deepcopy(stage); legacy['pair'].pop('checkpoint_layout')
for lifecycle in (None,dict(logical_bytes=8*1024**2,regular_files=68,directories=16,max_file_bytes=4*1024**2)):
    k=kwargs|{'lifecycle_reservation':lifecycle}
    check('legacy_actual_outputs_identical_'+str(lifecycle is not None),normalized(n.resolve(legacy,**k))==normalized(o.resolve(legacy,**k)))
selected=n.resolve(stage,**kwargs); prior=o.resolve(stage,**kwargs)
x=selected['residual_domains']['checkpoint_retention']
check('selected_file_slots_25221',x['regular_files']==25221)
check('selected_scratch_slots_264',x['scratch_files']==264)
check('selected_numeric_files_132',4*((8402640+262144-1)//262144)==132)
check('selected_constant_563',15+2+2*(132+3)+12+2*132==563)
check('native_1GiB',kwargs['native_file_bytes']==1073741824)
check('overlap_2K',x['additional_scratch_bytes']==2*stage['pair']['max_checkpoint_bytes']==538195968)
check('directories_5677',x['directories']==5677)
normalized_selected=normalized(selected); normalized_prior=normalized(prior)
for key in ('regular_files','scratch_files'): normalized_selected['residual_domains']['checkpoint_retention'][key]=normalized_prior['residual_domains']['checkpoint_retention'][key]
check('selected_only_two_file_fields_changed',normalized_selected==normalized_prior)
(HERE/'CHECKS01.json').write_text(json.dumps(dict(status='NARROW_SOURCE_ACCEPTED',checks=checks,source_sha256=sources,selected_checkpoint_retention=x,scope='Stdlib metadata only; no real arrays, numerical/native execution, claims, admission, budget rerun or financial conclusion.'),indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(status='PASS',checks=len(checks)),sort_keys=True))
