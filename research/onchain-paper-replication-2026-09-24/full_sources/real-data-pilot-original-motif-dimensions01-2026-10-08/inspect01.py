"""One bounded metadata inspection of preserved original JSON; no array loading."""
from pathlib import Path
import ast, datetime, hashlib, json, os, stat, subprocess, sys, types
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3]
D=F/'real-data-pilot-final19-2026-10-08';SOURCE='123e259a998a4aac4817b661434b1ef16c94c999'
PARSER=R/'tradingagents/research/onchain_replication/original_dictionary.py'
cache={};before={};after={}
def digest(b):return hashlib.sha256(b).hexdigest()
def identity(s):return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink,mode=stat.S_IMODE(s.st_mode))
def read(p,expected=None):
    p=Path(p);p=p if p.is_absolute() else R/p
    assert p.is_relative_to(R) and p.resolve(strict=True)==p
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=2*1024**2
    with p.open('rb') as f:
        assert identity(os.fstat(f.fileno()))==identity(s);b=f.read(2*1024**2+1)
        assert identity(os.fstat(f.fileno()))==identity(s)
    assert len(b)==s.st_size and identity(p.lstat())==identity(s)
    if expected is not None:assert digest(b)==expected
    before[str(p.relative_to(R))]=dict(sha256=digest(b),stat=identity(s));cache[p]=b;return b
def write(name,v):
    with (H/name).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
refs=json.loads(read(D/'ALL_INPUT_REFS01.json'))
control_path=R/refs['original_import']['path'];control=json.loads(read(control_path,refs['original_import']['sha256']))
gate=json.loads(read(D/'gate01.json'));exp=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261008-19']
for p in [D/'ALL_INPUT_REFS01.json',control_path,D/'gate01.json',PARSER]:
    if p not in cache:read(p,exp['source_files'][str(p.relative_to(R))])
    assert subprocess.check_output(['git','show',SOURCE+':'+str(p.relative_to(R))],cwd=R)==cache[p]
assert digest(cache[PARSER])=='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
assert control['original_claim']=='eth-paper-resource-pilot-20260924-02' and control['motif_count']==32 and control['sample_count']==512
assert control['refs']['dictionary']['sha256']=='7347dbd764144d3f9b2c934f802a6e9520224efd34ae8febc486803faf0cf1ad'
blobs={}
for role,pin in control['refs'].items():
    ref=refs[pin['input']];p=R/ref['path']
    assert p==Path(pin['original_path']) and ref['sha256']==pin['sha256']
    assert exp['inputs'][pin['input']]==ref
    blobs[role]=read(p,pin['sha256'])
# Import only exact authenticated stdlib parser source; no package initializer.
tree=ast.parse(cache[PARSER]);imports=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
assert all((n.module if isinstance(n,ast.ImportFrom) else n.names[0].name) in {'dataclasses','hashlib','json','math','datetime','threading'} for n in imports)
module=types.ModuleType('original_motif_metadata_parser');sys.modules[module.__name__]=module
exec(compile(cache[PARSER],str(PARSER),'exec'),module.__dict__)
validated=module.validate(control,blobs)
dictionary=module.parse(blobs['dictionary']);samples=module.parse(blobs['samples']);result=module.parse(blobs['dictionary_result']);terminal=module.parse(blobs['terminal'])
assert result['status']=='complete' and terminal['status']==validated.original_terminal=='failed'
rows=[]
for index,(g,sample_index) in enumerate(zip(dictionary['representatives'],validated.representative_indices,strict=True)):
    nodes,edges=module._graph(g)
    assert g==samples['graphs'][sample_index] and sample_index in dictionary['memberships'][index]
    rows.append(dict(motif_index=index,original_sample_index=sample_index,node_count=nodes,edge_count=edges,
        node_feature_width=4,edge_feature_width=g['edge_width'],node_feature_shape=[nodes,4],edge_feature_shape=[edges,g['edge_width']],edge_index_shape=[2,edges],
        representative_json_sha256=digest(module.canonical(g)),indexed_shape_valid=True))
assert len(rows)==32 and len({x['original_sample_index'] for x in rows})==32
for p,b in cache.items():
    s=p.lstat()
    with p.open('rb') as f:
        assert identity(os.fstat(f.fileno()))==identity(s);now=f.read(2*1024**2+1)
        assert identity(os.fstat(f.fileno()))==identity(s)
    record=dict(sha256=digest(now),stat=identity(s));assert now==b and record==before[str(p.relative_to(R))] and identity(p.lstat())==identity(s)
    after[str(p.relative_to(R))]=record
assert not any(n in sys.modules for n in ['numpy','torch','tradingagents.research','tradingagents.research.lifecycle'])
dimensions=dict(schema_version=1,kind='original32-motif-dimensions-metadata-v1',decision='accepted-metadata-only',
    original_claim=control['original_claim'],original_source=control['original_source'],original_parent_status='failed',original_dictionary_component_status='complete',
    original_dictionary_json_sha256=digest(blobs['dictionary']),original_dictionary_identity=validated.dictionary_identity,original_sample_identity=validated.sample_identity,
    original_bundle_sha256=validated.bundle_sha256,original_sample_count=512,motif_count=32,motifs=rows,
    interpretation='Directed edges retained including multiplicity; node count includes each original representative center. Dimensions are exact preserved JSON shapes, not newly sampled/clumped/matched graphs.',
    qualification='Metadata only. No original data rewritten, resampling/clustering/matching/fitting, arrays, attributes or address output. No new numerical authority, representation completion, cap amendment, reduction or resource/runtime capacity conclusion.')
write('MOTIF_DIMENSIONS01.json',dimensions)
review=dict(schema_version=1,decision='accepted-metadata-only',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    current_reference_source=SOURCE,parser=dict(path=str(PARSER.relative_to(R)),sha256=digest(cache[PARSER]),entry='validate(policy, blobs), parse, _graph; stdlib only'),
    extraction_parser=dict(path=str(Path(__file__).resolve().relative_to(R)),sha256=digest(Path(__file__).read_bytes())),
    before=before,after=after,all_before_after_hashes_and_stats_equal=True,
    joins=['Committed final19 gate/control/all-input refs at actual19 source123e259a','Exact eleven original public JSON bodies bounded2MiB each and16MiB aggregate via genuine original_dictionary.validate','Closed FAILED parent claim/gate/source/terminal joins; independently COMPLETE dictionary result','Dictionary/sample config, source graph, RNG/semantic identities and exact membership partition over512 retained samples','Each of32representatives is a unique exact retained sample member; indexed node/edge/feature shapes valid'],
    output=dict(path=str((H/'MOTIF_DIMENSIONS01.json').relative_to(R)),sha256=digest((H/'MOTIF_DIMENSIONS01.json').read_bytes())),
    limitations=['Hash/stat before and after observations do not establish writer exclusion or atomic historical snapshot.','Raw original JSON values were parsed only for genuine metadata validation and shape joins; no addresses or numerical attributes emitted.','No NumPy/Torch/research lifecycle imported; no runtime/memory measurement or universality/resource-capacity conclusion.','No new Owner, ResearchRun, native job, network, grant, representation completion or scientific re-execution.'])
write('REVIEW01.json',review)
write('MANIFEST01.json',dict(schema_version=1,decision='accepted-metadata-only',files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in sorted(H.iterdir()) if p.is_file()}))
print(json.dumps(dict(decision=review['decision'],motifs=32,node_count_range=[min(x['node_count'] for x in rows),max(x['node_count'] for x in rows)],edge_count_range=[min(x['edge_count'] for x in rows),max(x['edge_count'] for x in rows)],dimensions_sha256=review['output']['sha256'],review_sha256=digest((H/'REVIEW01.json').read_bytes())),sort_keys=True))
