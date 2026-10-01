"""Freeze retained resource inputs from compact evidence; no array or outcome reads."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
BASE='research/onchain-paper-replication-2026-09-24/'
FULL=BASE+'full_sources/'
COVERAGE=FULL+'resource-coverage-05-2026-09-30/coverage.json'

def require(ok,message):
    if not ok:raise ValueError(message)

def dimensions(manifest,verification):
    require(verification['status']=='complete','graph verification incomplete')
    require(manifest['graph_hash']==verification['graph_hash'],'graph identity differs')
    nodes,edges=verification['nodes'],verification['directed_edges']
    require(type(nodes) is int and nodes>0 and type(edges) is int and edges>=0,'invalid graph dimensions')
    sizes={k:v['bytes'] for k,v in manifest['arrays'].items()}
    require(set(sizes)=={'node_features','node_ids','edge_index','edge_features','edge_aggregates'},'graph member denominator differs')
    require(all(type(n) is int and n>0 for n in sizes.values()),'invalid array extent')
    require(sum(sizes.values())==verification['array_bytes'],'verified array byte sum differs')
    return {'nodes':nodes,'directed_edges':edges,'saved_array_file_bytes':sum(sizes.values()),
        'mcm_float32_payload_bytes':nodes*32*4,'mcm_float64_payload_bytes':nodes*32*8,
        'mcm_pair_evaluations':nodes*32}

def build(root):
    root=Path(root).resolve();pins={}
    def read(name,sha=None,json_body=True):
        path=root/name
        require(path.resolve()==path and path.is_file(),'compact evidence path missing or redirected: '+name)
        require(path.stat().st_size<=4*1024*1024,'compact metadata allowance exceeded')
        raw=path.read_bytes();actual=hashlib.sha256(raw).hexdigest()
        require(sha is None or sha==actual,'compact evidence hash differs: '+name)
        pins[name]={'sha256':actual,'bytes':len(raw)}
        return json.loads(raw) if json_body else None
    coverage=read(COVERAGE);requirements=coverage['requirements']
    require(len(requirements)==109 and len({r['original_id'] for r in requirements})==109,'original denominator differs')
    pending=[r for r in requirements if not r['supported']]
    require(len(pending)==coverage['remaining_resource_requirements']==32,'pending denominator differs')
    original=read(BASE+'config/dictionary.json');matching=read(BASE+'config/matching-stable.json')
    require(original['sample_count']==512 and original['size']==32,'original resource dictionary settings differ')
    legacy=read(FULL+'legacy-array-checker-2026-09-30/closure01.json')
    rows=[]
    for requirement in requirements:
        if requirement['stage']!='decode_graph':continue
        evidence=requirement['evidence'];week=requirement['date']
        for ref in evidence:read(ref['path'],ref['sha256'],not ref['path'].endswith('.md'))
        if requirement['requirement_evidence']=='original_completed_phase':
            result=read(evidence[0]['path'],evidence[0]['sha256'])
            manifest_path=str(Path(result['details']['graph_manifest']).relative_to(root))
            manifest_sha=result['details']['graph_manifest_sha256']
            verification_path=FULL+'legacy-array-checker-2026-09-30/verification01/payload/'+week+'.json'
            verification=read(verification_path)
            matches=[g for g in legacy['graphs'] if g['week']==week]
            require(len(matches)==1 and matches[0]=={k:v for k,v in verification.items() if k!='week'},'legacy verification closure differs')
        else:
            selected=[r for r in evidence if r['path'].endswith('/manifest.json')]
            verified=[r for r in evidence if '/graph-verification' in r['path'] and r['path'].endswith('/result.json')]
            require(len(selected)==len(verified)==1,'unique graph and verifier required')
            manifest_path,manifest_sha=selected[0]['path'],selected[0]['sha256']
            verification_path=verified[0]['path'];verification=read(verification_path,verified[0]['sha256'])
        manifest=read(manifest_path,manifest_sha)
        require(verification.get('manifest_sha256',verification.get('graph_manifest_sha256'))==manifest_sha,'verifier manifest join differs')
        require(manifest['metadata']['asset']=='ETH' and manifest['metadata']['start_utc'][:10]==week,'graph asset/week differs')
        rows.append({'week':week,'graph_hash':manifest['graph_hash'],'manifest':manifest_path,'manifest_sha256':manifest_sha,
            'verification':verification_path,'pending_requirement_ids':[r['original_id'] for r in pending if r['date']==week],
            **dimensions(manifest,verification)})
    require(len(rows)==9 and len({r['week'] for r in rows})==9,'nine unique retained weeks required')
    require(sorted(n for row in rows for n in row['pending_requirement_ids'])==sorted(r['original_id'] for r in pending),'pending graph mapping differs')
    return {'schema_version':1,'scope':'Compact saved-evidence input binding and arithmetic only; no empirical execution, numerical reads or new resource coverage.',
        'execution_admitted':False,'graphs':rows,'inputs':pins,'supported_requirements':77,'pending_requirements':pending,
        'original_settings':{'sample_count':512,'motifs':32,'seed':11,'maximum_neighborhood_nodes':original['maximum_neighborhood_nodes'],'max_pair_entries':matching['max_pair_entries']},
        'totals':{k:sum(r[k] for r in rows) for k in ('nodes','directed_edges','saved_array_file_bytes','mcm_float32_payload_bytes','mcm_float64_payload_bytes','mcm_pair_evaluations')},
        'qualification':'File bytes and dense MCM payload arithmetic are not measured RSS, working disk, numerical dtype selection, runtime or proof that all graphs must be resident together. Historical array-verification qualifications remain unchanged.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
    result=build(ROOT)
    with args.output.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({'graphs':len(result['graphs']),'pending':len(result['pending_requirements']),'totals':result['totals']},sort_keys=True))
