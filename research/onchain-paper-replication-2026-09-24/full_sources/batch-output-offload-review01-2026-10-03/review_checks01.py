"""Independent metadata arithmetic and tiny byte codec checks; no numerical imports."""
from pathlib import Path
import hashlib,json,ast
P=Path(__file__).resolve().parent;S=P.with_name('batch-output-offload-investigation-2026-10-03');R=P.parents[3]
def h(b):return hashlib.sha256(b).hexdigest()
m=json.loads((S/'MANIFEST01.json').read_bytes())
for row in m['files']:
 b=(S/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
c=json.loads((S/'census01.json').read_bytes())
for row in c['source_references']:
 b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
i=json.loads((R/'research/onchain-paper-replication-2026-09-24/full_sources/native-resource-admission-2026-10-01/inputs02.json').read_bytes());g={r['week']:r for r in i['graphs']}
assert len(c['rows'])==9 and len({r['week'] for r in c['rows']})==9
for row in c['rows']:
 n=g[row['week']]['nodes'];assert row['nodes']==n and row['cells']==n*32
 for key,factor in [('score_batch_f64_bytes',8),('raw_mcm_f32_bytes',4),('graph_artifact_mcm_f32_payload_bytes',4),('non_tail_payload_bytes',16),('tail_payload_bytes',80)]:assert row[key]==factor*n*32
nodes=sum(r['nodes'] for r in c['rows']);cells=32*nodes
assert nodes==18046816 and cells==577498112 and 96*cells==55439818752
source=(S/'member_ranges01.py').read_bytes();tree=ast.parse(source)
assert {n.name for n in ast.walk(tree) if isinstance(n,ast.alias)}=={'hashlib','json','re','PurePosixPath'}
ns={};exec(compile(tree,str(S/'member_ranges01.py'),'exec'),ns)
b=bytes(range(24));v={'schema_version':1,'kind':'non-tail-exact-member-plan-v1','role':'score-batch','owner':'ab'*32,'stage_sha256':'cd'*32,'container_sha256':'ef'*32,'scope':{k:'12'*32 for k in ns['SCOPES']},'path':'a/chunk.bin','dtype':'<f8','order':'row-major','rows':1,'motifs':32,'start_cell':0,'cells':3,'header_bytes':0,'bytes':24,'sha256':h(b),'chunk_bytes':8}
assert ns['verify_parts'](v,[b[:8],b[8:16],b[16:]])['execution_admitted'] is False
for parts in [[b[8:16],b[:8],b[16:]],[b[:8]], [b[:8],b[8:16],b[16:],b'']]:
 try:ns['verify_parts'](v,parts)
 except ValueError:pass
 else:raise AssertionError('incorrect stream accepted')
fatal=MemoryError('review sentinel')
def broken():
 yield b[:8]
 raise fatal
try:ns['verify_parts'](v,broken())
except MemoryError as got:assert got is fatal
else:raise AssertionError('fatal lost')
try:ns['activate'](v)
except RuntimeError:pass
else:raise AssertionError('activation accepted')
q=ns['validate'](v);v['scope']['graph']='98'*32;assert q['scope']['graph']!='98'*32
# Explicitly disclose this plan-schema path limitation, not an actual file capability.
assert ns['validate'](dict(v,path='.'))['path']=='.'
print(json.dumps({'manifest_sha256':h((S/'MANIFEST01.json').read_bytes()),'manifest_bodies':len(m['files']),'source_metadata_refs':len(c['source_references']),'weeks':9,'nodes':nodes,'cells':cells,'f64':8*cells,'raw_f32':4*cells,'artifact_f32_payload':4*cells,'non_tail':16*cells,'tail':80*cells,'combined':96*cells,'codec_exact_stream_refusals_and_fatal_identity':True,'activation_refused':True,'plan_accepts_dot_path':True,'no_numerical_imports_arrays_transport_or_jobs':True},indent=2))
