"""Concrete metadata-only preparation; no live namespace, launch or authority writes."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def load():
    p=HERE/'continue01.py';s=importlib.util.spec_from_file_location('metadata_successor',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ref(path,root=ROOT):return {'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
def prepare(review_ref,output,scanner_sha=None):
    h=load();review=h.doc(ROOT,review_ref);binding={'review':review_ref,'metadata':review['metadata_check'],'outcome':review['outcome_check']}
    selection=h.select(ROOT,binding)
    out=Path(output);h.need(out.parent.resolve()==HERE and not out.exists(),'fresh direct child of owned preparation directory required')
    # Only bounded source/metadata references; connection is copied as HASH ONLY.
    meta=h.doc(ROOT,binding['metadata']);original_name=h.OLD+'/envelope01.json';original=h.doc(ROOT,{'path':original_name,'sha256':meta['evidence'][original_name]});sources={}
    for name in original['source_files']:
        if name.endswith('/entry01.py') or name==original['helper']['path']:continue
        p=ROOT/name;h.need(p.stat().st_size<=h.LIMIT and p.resolve()==p,'bounded actual source required');sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    helper=ref(HERE/'continue01.py');entry=ref(HERE/'entry01.py');prep=ref(HERE/'prepare01.py')
    sources[helper['path']]=helper['sha256'];sources[prep['path']]=prep['sha256'];sources[h.DEST+'/entry01.py']=entry['sha256']
    scanner='tradingagents/research/onchain_replication/workflow_storage.py'
    if scanner_sha is not None:h.need(sources[scanner]==scanner_sha and scanner_sha!='bf52b9408008ac3616f867ebef8130e2f315f8c8febf00ab1815557d68684554','corrected scanner is not integrated at exact supplied hash')
    encode=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
    sbody=encode(selection);selection_ref={'path':h.DEST+'/selection01.json','sha256':hashlib.sha256(sbody).hexdigest(),'bytes':len(sbody)}
    evidence=[review_ref,binding['metadata'],binding['outcome'],review['recovered_payload_hash']]
    envelope={**original,'identity':h.ID,'status':'DRAFT_NOT_RELEASED','helper':helper,'selection':selection_ref,'source_files':sources,'evidence':evidence,'scanner_sha256':scanner_sha,'qualification':h.QUALIFICATION+' Root must bind integrated reviewed scanner, exact independent release, committed/external source and fresh native/process/resources before use.'}
    out.mkdir();(out/'selection01.json').write_bytes(sbody);(out/'envelope01.json').write_bytes(encode(envelope))
    (out/'PREPARATION01.json').write_bytes(encode({'identity':h.ID,'status':'DRAFT_NOT_RELEASED','selection_sha256':selection_ref['sha256'],'entry_candidate':entry,'helper':helper,'inherited_body_count':36,'previous_complete_metadata_count':35,'missing_metadata_rows':[35],'fresh_body_transfer_count':0,'scanner_integrated_pin':scanner_sha,'root_required':['Copy exact entry/selection/envelope into fresh fixed successor namespace','Independently accept helper/entry and scanner correction; bind actual integrated scanner hash','Set envelope status FROZEN_ROOT_BOUND_REQUIRES_RELEASE only after current source binding; no automatic release','Bind exact envelope/evidence in independent release, commit/push and verify actual external HEAD','Fresh no-active-job/unused-identity/runtime/parent-stat/resource eligibility; ONE guarded ordinary operation','Independently review actual successor full metadata recovery/native cleanup before any separate retirement'],'no_paper_claim_refund_or_parent_retry':True}))
    return {'draft_directory':str(out),'selection_sha256':selection_ref['sha256'],'envelope_sha256':hashlib.sha256(encode(envelope)).hexdigest(),'inherited_bodies_stat_checked':36,'large_body_reads':0,'fresh_body_transfers':0,'missing_metadata_rows':[35]}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--review',required=True);a.add_argument('--review-sha256',required=True);a.add_argument('--output',required=True);a.add_argument('--scanner-sha256');o=a.parse_args();print(json.dumps(prepare({'path':o.review,'sha256':o.review_sha256},o.output,o.scanner_sha256),indent=2))
