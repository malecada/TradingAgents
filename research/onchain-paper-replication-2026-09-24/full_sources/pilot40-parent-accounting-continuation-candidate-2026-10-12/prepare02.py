from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[3];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';parent='eth-paper-real-data-end-to-end-resource-20261012-39';D=R/'research_runs'/parent
G=R/'research_artifacts/onchain_representations/ada9fbd6764c8dc113bf837ff9cc71296dd9c09e6af2a9da4d7a841a2e91329f'/parent/'compact/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
claim=json.loads((D/'claim.json').read_text());failed=json.loads((D/'failed.json').read_text())
h=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37'
paths={'traceback':R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/parent/'guard/child.log','return_review':F/'pilot39-outcome-increment37-review-2026-10-12/RETURN_REVIEW01.json','recovery':h/'FRESH_GIT_RECOVERY37.json','selection':h/'SELECTION37.json','capture':h/'CAPTURE37.json','guard_final':R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/parent/'guard/final.json'}
paths.update(('output:'+name,D/'outputs'/name) for name in failed['output_sha256'])
evidence={k:dict(path=str(p.relative_to(R)),sha256=sha(p)) for k,p in paths.items()}
sources={str(Path('tradingagents/research/onchain_replication')/p.name):sha(p) for p in sorted((P/'original_source').iterdir()) if p.suffix=='.py'}
assert all(claim['experiment']['source_files'][k]==v for k,v in sources.items())
commits=[json.loads((G/f'matching/{i:08d}.prefix.json').read_text()) for i in range(16)]
refs=[c['score_sha256']+[c['origin_sha256'],c['summary_sha256'],sha(G/f'matching/{i:08d}.prefix.json')] for i,c in enumerate(commits)]
last=commits[-1];costs={k:last[k] for k in ('checkpoint_attempts','checkpoint_reserved_bytes')}|last['operation_counters']
contract=dict(format='original39-post-prefix-failure-v1',parent=parent,claim_sha256=sha(D/'claim.json'),failed_sha256=sha(D/'failed.json'),evidence=evidence,sources=sources,batches=refs,costs=costs,stop=65536)
(P/'EXACT_CONTRACT02.json').write_text(json.dumps(contract,indent=2)+'\n')
helper='''
def _original39_accounting(raw, m, review, claim, failed, evidence_raw, source_raw):
    """Finite byte proof only; called after genuine admission and both recoveries."""
    fixed=_ORIGINAL39
    a=_json(raw)
    require(set(a)=={'format','parent_experiment','parent_claim_sha256','parent_failed_sha256',
        'evidence','source_bodies','spent_counters','retained_partial_work','preserved_unknowns'},
        'derived accounting schema differs')
    require(a['format']==fixed['format']==m['parent_accounting_mode']
        and a['parent_experiment']==m['parent_experiment']==fixed['parent']
        and a['parent_claim_sha256']==fixed['claim_sha256']
        and a['parent_failed_sha256']==fixed['failed_sha256']
        and review['parent_accounting_mode']==fixed['format']
        and review['parent_accounting_sha256']==digest(raw), 'derived accounting identity/review differs')
    require(digest(body(claim))==fixed['claim_sha256'] or claim==_json(evidence_raw['claim']),
        'derived original claim differs')
    require(digest(evidence_raw['claim'])==fixed['claim_sha256']
        and digest(evidence_raw['failed'])==fixed['failed_sha256']
        and failed==_json(evidence_raw['failed']), 'derived original terminal differs')
    require(set(a['evidence'])==set(fixed['evidence']) and set(evidence_raw)==set(fixed['evidence'])|{'claim','failed'},
        'derived recovered evidence roster differs')
    for key,pin in fixed['evidence'].items():
        require(a['evidence'][key]['sha256']==pin['sha256'] and digest(evidence_raw[key])==pin['sha256'],
            'derived original evidence bytes differ')
        if key.startswith('output:'):
            require(failed['output_sha256'][key[7:]]==pin['sha256'],'derived original output seal differs')
    selection=_json(evidence_raw['selection']);returned=_json(evidence_raw['return_review'])
    rows={r['path']:r for r in selection['rows'] if r['type']=='regular'}
    for key in ('traceback','guard_final'):
        pin=fixed['evidence'][key]
        require(rows[pin['path']]['sha256']==pin['sha256'],'derived raw original outside recovered selection')
    require(returned['decision']=='accepted' and returned['actual_operations']==13
        and returned['regular_files']==318 and returned['returned_typed_body_checks'] is True,
        'derived full external return absent')
    for key in ('recovery','selection','capture'):
        pin=fixed['evidence'][key]
        require(returned['evidence'][pin['path']]==pin['sha256'],'derived return review join differs')
    require(set(a['source_bodies'])==set(source_raw)==set(fixed['sources']),'derived original source roster differs')
    for path,sha in fixed['sources'].items():
        require(claim['experiment']['source_files'][path]==sha
            and a['source_bodies'][path]['sha256']==sha and digest(source_raw[path])==sha,
            'derived original source differs')
    require(m.get('provenance_mode','durable-commit')=='durable-commit'
        and len(m['batches'])==16 and [[r['sha256'] for r in batch] for batch in m['batches']]==fixed['batches'],
        'derived exact sixteen durable batches required')
    require(a['spent_counters']==m['spent_counters']==fixed['costs']
        and a['retained_partial_work']=={k:0 for k in fixed['costs']}
        and a['preserved_unknowns']==['telemetry','cache','transport','outer_disposition'],
        'derived five-counter no-tail scope differs')
    return a

'''
# No reserialization assumption for original claim: compare decoded original bytes directly.
helper=helper.replace("digest(body(claim))==fixed['claim_sha256'] or claim==_json(evidence_raw['claim'])", "claim==_json(evidence_raw['claim'])")
source=(P/'BASELINE_batched_continuation.py').read_text();point=source.index('\ndef _authority(')
source=source[:point]+'\n_ORIGINAL39 = '+repr(contract)+'\n'+helper+source[point:]
old="    accounting_raw=registered(m['parent_accounting'])\n"
new=old+'''    if 'parent_accounting_mode' in m:
        require(m['parent_accounting_mode']==_ORIGINAL39['format'], 'unknown parent accounting mode')
        a=_json(accounting_raw)
        require(type(a) is dict and type(a.get('evidence')) is dict and type(a.get('source_bodies')) is dict
            and set(a['evidence'])==set(_ORIGINAL39['evidence'])
            and set(a['source_bodies'])==set(_ORIGINAL39['sources']), 'bounded derived proof roster required')
        evidence_raw={'claim':claim_raw,'failed':failed_raw}
        for key,ref in a['evidence'].items():evidence_raw[key]=registered(ref)
        source_raw={path:registered(ref) for path,ref in a['source_bodies'].items()}
        return _original39_accounting(accounting_raw,m,review,claim,failed,evidence_raw,source_raw)
'''
assert source.count(old)==1;source=source.replace(old,new)
(P/'batched_continuation.py').write_text(source)
print('Prepared exact-case source-only contract; no registered derived proof created')
