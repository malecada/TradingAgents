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
    pin=json.loads((HERE/'DEPENDENCIES02.json').read_text())[name];p=ROOT/pin['path'];s=p.read_bytes()
    need(hashlib.sha256(s).hexdigest()==pin['sha256'],'dependency differs: '+name)
    # Metadata adapters' sole new package import is resolved to the exact pinned
    # stdlib helper, without installing/importing the scientific package.
    text=s.decode();line='        from tradingagents.research.onchain_replication.archive_control_history import capacity\n'
    if name in ('builder','controls'):
        need(text.count(line)==1,'adapter import seam differs');text=text.replace(line,'')
    if name=='controls':
        read_line='        from tradingagents.research.onchain_replication.archive_read_control_capacity import capacity as read_capacity\n'
        need(text.count(read_line)==1,'packed scalar import seam differs');text=text.replace(read_line,'')
    m=types.ModuleType(name);m.__file__=str(p)
    if name in ('builder','controls'):m.capacity=load('history').capacity
    if name=='controls':m.read_capacity=load('read_capacity').capacity
    exec(compile(text,str(p),'exec'),m.__dict__);return m

def prepare(root,draft):
    """Full existing handoff with only selected adapters/history inventory added."""
    m=load('handoff');pin=json.loads((HERE/'DEPENDENCIES02.json').read_text())['handoff'];s=(ROOT/pin['path']).read_text()
    old="'transport':{k:tr[k] for k in ('max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes')},"
    need(s.count(old)==1,'handoff transport seam differs')
    s=s.replace(old,old[:-1]+"|({'control_history':tr['control_history']} if 'control_history' in tr else {}),")
    exec(compile(s,m.__file__,'exec'),m.__dict__);m.load=load
    return m.prepare(root,draft)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(description='Pinned metadata prepare only; no generation or admission.')
    a.add_argument('--prepare',type=Path,required=True);v=a.parse_args()
    with v.prepare.open('rb') as stream:body=stream.read(4*1024**2+1)
    need(len(body)<=4*1024**2,'metadata input too large')
    print(json.dumps(prepare(ROOT,json.loads(body)),sort_keys=True,allow_nan=False))
