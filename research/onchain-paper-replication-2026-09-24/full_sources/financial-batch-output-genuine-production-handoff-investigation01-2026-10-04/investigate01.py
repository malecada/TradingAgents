"""Finite source/metadata readback only. No imported project code or array bodies."""
import ast, hashlib, json, os, stat, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
MAIN=BASE.parents[2]
SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PKG='tradingagents/research/onchain_replication/'
CASE='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
checks=[]
def check(value,label):
    if not value: raise AssertionError(label)
    checks.append(label)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(path):
    check(path.is_absolute() and path.resolve()==path,'canonical '+str(path))
    before=path.lstat()
    check(stat.S_ISREG(before.st_mode) and 0<before.st_size<4*1024**2,'bounded regular '+str(path))
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        b=b''
        while len(b)<=before.st_size:
            q=os.read(fd,min(65536,before.st_size-len(b)+1))
            if not q:break
            b+=q
        sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        check(sig(before)==sig(os.fstat(fd))==sig(path.lstat()) and len(b)==before.st_size,'stable '+str(path))
    finally:os.close(fd)
    return b
gate_path=SRC/'fixture_inputs/financial_wrapper_claimedrun01/gates.json'
gate_raw=read(gate_path);gate=json.loads(gate_raw);experiment=gate['experiments'][CASE]
check(sha(gate_raw)=='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a','fixed actual gate')
check(len(experiment['source_files'])==338 and len(experiment['inputs'])==8,'actual map/input counts only, not full source verification')
head=subprocess.run(['git','-C',str(SRC),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
check(head=='0a2e7639b42b9423b90743feadcda4078aa21816','actual read-only Source HEAD')
names=['score_batches.py','mcm_score_stream.py','compact_mcm.py','compact_owner.py','matching_owner.py','imported_mcm_identity.py','compact_mcm_output.py','compact_mcm_publication.py','workflow_storage.py','compact_features.py','compact_graph_artifacts.py','model.py','training.py','archive_dispatch.py','archive_transport.py','archive_owner_seal.py','compact_stage.py']
paths=[SRC/PKG/n for n in names]
prepared={
 'batch-output-produced-f32-adapter-preparation02-2026-10-03':['completed_f32.py','compact_mcm.py','archive_non_tail.py','selected_non_tail_transport.py'],
 'batch-output-combined-worker-preparation01-2026-10-03':['held_score_consumer.py'],
 'batch-output-exact-member-reader-candidate02-2026-10-03':['exact_members02.py','owned_io.py'],
 'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03':['held_score_reader.py'],
 'batch-output-durable-context-preparation03-2026-10-03':['archive_non_tail.py','archive_dispatch.py','archive_transport.py'],
 'batch-output-transport-context-preparation03-2026-10-03':['non_tail_context.py'],
 'financial-batch-output-codec-spool-integration-preparation01-2026-10-04':['router04.py','codec01.py','local_store01.py','spool05.py'],
}
paths += [BASE/d/n for d,ns in prepared.items() for n in ns]
rows=[];bodies={}
for p in paths:
    raw=read(p);text=raw.decode();tree=ast.parse(text)
    key=str(p);bodies[key]=text
    functions=[]
    def visit(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                functions.append({'name':prefix+n.name,'line':n.lineno,'end_line':n.end_lineno})
                visit(n.body,prefix+n.name+'.')
    visit(tree.body)
    row={'path':key,'sha256':sha(raw),'bytes':len(raw),'mode':stat.S_IMODE(p.lstat().st_mode),'definitions':functions}
    if p.is_relative_to(SRC):
        relative=p.relative_to(SRC).as_posix()
        check(experiment['source_files'].get(relative)==sha(raw),'actual admitted source body '+relative)
        row['actual_gate_join']=True
    rows.append(row)
expected={'router04.py':'24bb42b49baba8ea330ced3864d28019a5b30745d5739de3cafc2cbea8a74454','codec01.py':'f10f6803a637735bc490de8846056a34e9090451d92773d075a7025b19bd3d55','local_store01.py':'ceec61446f678f8749fa1e24530b5b4e3e344a59cce75f7906e322f03dd8ad89','spool05.py':'704e26d5d35c546ce61438e0ba1597526f92e6b33fdb8719a2a2765c6f1cbd5f'}
for n,h in expected.items():check(next(r['sha256'] for r in rows if r['path'].endswith('codec-spool-integration-preparation01-2026-10-04/'+n))==h,'fixed router dependency '+n)
absent=['held_score_consumer.py','completed_f32.py','archive_non_tail.py','selected_non_tail_transport.py']
for n in absent:check(not os.path.lexists(SRC/PKG/n) and PKG+n not in experiment['source_files'],'prepared adapter absent from current source '+n)
inputs=[]
for role,ref in sorted(experiment['inputs'].items()):
    raw=read(SRC/ref['path']);check(sha(raw)==ref['sha256'],'actual input '+role)
    inputs.append({'role':role,**ref,'bytes':len(raw)})
job=json.loads(read(SRC/experiment['inputs']['execution_job']['path']))
census_path=BASE/'batch-output-offload-investigation-2026-10-03/census01.json'
census_raw=read(census_path);census=json.loads(census_raw)
nodes=sum(x['nodes'] for x in census['rows']);cells=32*nodes
check(len(census['rows'])==9 and nodes==18046816 and cells==577498112,'historical conditional nine-week denominator')
check(sum(x['non_tail_payload_bytes'] for x in census['rows'])==16*cells==9239969792,'three distinct non-tail raw payload populations')
check(96*cells==55439818752,'tails plus non-tail conditional logical lower bound')
for x in census['rows']:
    check(x['score_batch_f64_bytes']==8*x['cells'] and x['raw_mcm_f32_bytes']==4*x['cells'] and x['graph_artifact_mcm_f32_payload_bytes']==4*x['cells'],'historical week arithmetic '+x['week'])
def source(suffix):return next(v for k,v in bodies.items() if k.endswith(suffix))
check('return actual,stream.finish()' in bodies[str(SRC/PKG/'compact_mcm.py')] and 'held_score_consumer' not in bodies[str(SRC/PKG/'compact_mcm.py')],'current producer has no held codec call')
check("2+2*chunks<=ENTRIES" in source('candidate02-2026-10-03/exact_members02.py'),'original reader includes headers/start/terminal')
check("n in (2,3)" in source('combined-worker-preparation01-2026-10-03/held_score_consumer.py'),'combined tiny population restriction retained')
check("1<=n<=4" in source('adapter-preparation02-2026-10-03/completed_f32.py'),'raw standalone tiny restriction retained')
check("disposition_authority':False,'local_bytes_retired':0" in source('adapter-preparation02-2026-10-03/selected_non_tail_transport.py'),'typed source transport explicitly no retirement')
check('target.check()' in source('held-score-reader-preparation01-2026-10-03/held_score_reader.py'),'full target checks retained in prepared f64 reader')
check('produced._check()' in source('adapter-preparation02-2026-10-03/completed_f32.py'),'genuine full produced check retained')
result={'status':'SOURCE_HANDOFF_INVESTIGATION_ONLY','current_source':str(SRC),'head':head,'gate_sha256':sha(gate_raw),'experiment_id':CASE,'source_map_count':338,'source_bodies_checked':len(names),'inputs':inputs,'current_job_kind':job['kind'],'current_job_payload_keys':sorted(job['payload']),'absent_prepared_modules':absent,'sources':rows,'historical_census':{'path':str(census_path),'sha256':sha(census_raw),'rows':census['rows'],'scope':'conditional nine saved metadata weeks, not current Target inventory or produced bytes'},'checks':checks,'check_count':len(checks),'unperformed':['numerical import/execution','genuine authority construction or admission','whole 338-source rerun','byte transfer/recovery','capacity measurement','retirement/deletion','current completed Target inventory']}
for name,obj in [('READBACK01.json',result),('SOURCE_BODIES01.json',bodies)]:
    with (OUT/name).open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'source_bodies':len(rows),'source_bytes':sum(r['bytes'] for r in rows),'current_job_kind':job['kind'],'readback_sha256':sha((OUT/'READBACK01.json').read_bytes())},sort_keys=True))
