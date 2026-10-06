"""Pinned metadata successor only. Unknown graphs/baseline never become authority."""
import copy,hashlib,json,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
F=HERE.parent
HISTORY={'schema_version':1,'format':'bounded-archive-control-history-v1','assumption':'closed-history sampled; no writer exclusion; mandatory boundary full-byte audits','success_control_bytes':1024,'success_diagnostic_bytes':2048,'shard_bytes':4194304,'full_interval_ms':1000,'max_stale_ms':60000,'max_callbacks_between_full':4096}
DURABILITY={'schema_version':1,'scope':'resource-pilot-only','pair_records':1024,'tail_records':1024,'max_interval_ms':1000}
def need(v,m):
    if not v:raise ValueError(m)
def raw(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def load(name):
    pin=json.loads((HERE/'DEPENDENCIES01.json').read_text())[name];p=ROOT/pin['path'];s=p.read_bytes()
    need(hashlib.sha256(s).hexdigest()==pin['sha256'],'dependency differs: '+name)
    # Metadata adapters' sole new package import is resolved to the exact pinned
    # stdlib helper, without installing/importing the scientific package.
    text=s.decode();line='        from tradingagents.research.onchain_replication.archive_control_history import capacity\n'
    if name in ('builder','controls'):
        need(text.count(line)==1,'adapter import seam differs');text=text.replace(line,'')
    m=types.ModuleType(name);m.__file__=str(p)
    if name in ('builder','controls'):m.capacity=load('history').capacity
    exec(compile(text,str(p),'exec'),m.__dict__);return m

def prepare(root,draft):
    """Full existing handoff with only selected adapters/history inventory added."""
    m=load('handoff');pin=json.loads((HERE/'DEPENDENCIES01.json').read_text())['handoff'];s=(ROOT/pin['path']).read_text()
    old="'transport':{k:tr[k] for k in ('max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes')},"
    need(s.count(old)==1,'handoff transport seam differs')
    s=s.replace(old,old[:-1]+"|({'control_history':tr['control_history']} if 'control_history' in tr else {}),")
    exec(compile(s,m.__file__,'exec'),m.__dict__);m.load=load
    return m.prepare(root,draft)

def generate(out):
    need(not out.exists() and out.parent==HERE,'fresh owned output only');out.mkdir()
    base=F/'real-data-pilot-selected-feature-protocol01-2026-10-06/draft07'
    d=json.loads((base/'INPUT_DRAFT01.json').read_text());p=d['protocol'];sel=load('selected');b=load('builder')
    index=F/'real-data-pilot-current-graph-counts03-2026-10-06/INDEX_DRAFT01.json'
    ix=json.loads(index.read_text());count=b.metadata(ROOT,ix['may23_count'])
    week='2022-05-23T00:00:00Z';mp=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220523-20261005-01/graph-2022-05-23/manifest.json'
    def ref(path):return {'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    d['graphs'][week]={'role':'graph_20220523','manifest':ref(mp),'node_count':ix['may23_count']}
    counts={}
    for w,g in d['graphs'].items():
        if g is None:counts[w]=None;continue
        n=b.metadata(ROOT,g['node_count']);man=b.metadata(ROOT,g['manifest'])
        need(n['graph_manifest_sha256']==g['manifest']['sha256'] and n['node_features_sha256']==man['arrays']['node_features']['sha256'],'count chain differs')
        counts[w]=n['rows']
    p['typed_allocations']['by_week'][week]=sel.kind_alloc(count['rows'])
    history=load('history');history.validate(HISTORY);load('durability').policy(DURABILITY)
    p['transport_limits']['control_history']=HISTORY
    old=b.metadata(ROOT,p['references']['mcm_policy']);new=copy.deepcopy(old);new.update(schema_version=2,durability=DURABILITY)
    path=out/'mcm_policy.json';path.write_bytes(raw(new));p['references']['mcm_policy']=ref(path)
    inverse=copy.deepcopy(new);inverse.pop('durability');inverse['schema_version']=1
    need(inverse==old,'scientific MCM parity differs')
    # Five-known-graph lower bound; never extrapolate unknown counts.
    kinds=[k for w,v in p['typed_allocations']['by_week'].items() if v for k in v.values()]
    c=max(n for n in counts.values() if n is not None)*32;E=2*c+160;Q=(E+49151)//49152
    commands=4*sum(k['max_chunks'] for k in kinds)+8*Q*20
    bounds=history.capacity(HISTORY,commands)
    arithmetic={'status':'INCOMPLETE_LOWER_BOUND_NOT_CAPACITY','counts':counts,'missing_weeks':[w for w,n in counts.items() if n is None], 'known_allocation_commands_lower_bound':commands,'selected_retained_transport_bounds':bounds,'legacy_retained_control_bound_at_same_commands':131072*(8+4*commands),'typed_attempt_metadata_lower_bound':4*8192*sum(k['max_chunks'] for k in kinds),'frozen_storage_limits':b.metadata(ROOT,p['references']['execution_job'])['resources']['storage_budget']['limits'],'full_seven_graph_total':None,'physical_baseline':p['physical_baseline'],'cap_changes':False}
    (out/'INPUT_DRAFT01.json').write_bytes(raw(d));(out/'ARITHMETIC01.json').write_bytes(raw(arithmetic))
    (out/'PARITY01.json').write_bytes(raw({'mcm_original':old,'inverse_equal':True,'other_template_references_unchanged':True,'source_helpers_require_eager_archive_preflight':True,'original_protocol_preserved':str(base)}))
    return d,arithmetic
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--generate',type=Path);a.add_argument('--prepare',type=Path);v=a.parse_args()
    if v.generate:generate(v.generate.resolve())
    elif v.prepare:print(json.dumps(prepare(ROOT,json.loads(v.prepare.read_text())),sort_keys=True))
    else:a.error('select --generate or --prepare')
