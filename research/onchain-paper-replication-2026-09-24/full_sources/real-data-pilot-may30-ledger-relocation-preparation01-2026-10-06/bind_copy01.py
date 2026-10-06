"""Root metadata binding after installing exact reviewed entry/helper/selection."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
B='research/onchain-paper-replication-2026-09-24'
DEST=B+'/full_sources/real-data-pilot-may30-ledger-relocation01-2026-10-06'
BASE=B+'/full_sources/real-data-pilot-fifth-graph-failed-get-duplicates-retirement-preparation01-2026-10-06'
def ref(path):
    p=ROOT/path
    if p.resolve(strict=True)!=p or not p.is_file() or p.stat().st_size>4*1024**2:raise ValueError('canonical bounded binding required')
    return {'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
if __name__=='__main__':
    old=json.loads((ROOT/B/'storage/real-pilot-fifth-graph-failed-preservation-20261006-01/envelope01.json').read_bytes())
    selection=ref(DEST+'/SELECTION01.json');c=json.loads((ROOT/selection['path']).read_bytes())
    if c['identity']!='real-pilot-may30-ledger-relocation-20261006-01' or c['status']!='FROZEN_FOR_REVIEW':raise ValueError('exact selected copy required')
    helper=ref(DEST+'/relocate01.py');entry=ref(DEST+'/entry01.py')
    # Retain accepted supervisor/runtime source closure, replacing the prior transfer entry/helper.
    drop={old['helper']['path'],old['transport']['path']}
    source={p:h for p,h in old['source_files'].items() if p not in drop and not p.endswith('/entry01.py')}
    for p,h in source.items():
        if ref(p)['sha256']!=h:raise ValueError('inherited source changed; Root must resolve: '+p)
    source.update({helper['path']:helper['sha256'],entry['path']:entry['sha256'],BASE+'/retire01.py':ref(BASE+'/retire01.py')['sha256']})
    evidence=[{'path':p,'sha256':h} for p,h in c['recovery_selection']['evidence'].items()]
    print(json.dumps({'identity':c['identity'],'phase':'copy','selection':selection,'helper':helper,'environment':old['environment'],'source_files':source,'evidence':evidence},indent=2))
