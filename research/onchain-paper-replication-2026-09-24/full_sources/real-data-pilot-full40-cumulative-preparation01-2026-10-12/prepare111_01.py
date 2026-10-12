"""Finite Root111 accounting preparation; reads metadata only, never claims."""
import copy
import hashlib
import json
import os
from pathlib import Path

ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-full38-cumulative-preparation01-2026-10-12'
NAMES=['eth-paper-real-data-end-to-end-resource-20261012-40']
def read(p):
    assert p.resolve(strict=True)==p and p.is_file() and not p.is_symlink() and p.stat().st_size<=4*1024**2
    def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    before=identity(p.stat());b=p.read_bytes();assert len(b)<=4*1024**2 and before==identity(p.stat());return b
def load(p):return json.loads(read(p))
def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(read(p)).hexdigest()}
def save(n,x):
    with (HERE/n).open('x') as h:json.dump(x,h,sort_keys=True,indent=2);h.write('\n')
def main():
    assert HERE==F/'real-data-pilot-full40-cumulative-preparation01-2026-10-12'
    extension=load(OLD/'EXTENSION_PROPOSED110_01.json');allocation=load(OLD/'CUMULATIVE_ALLOCATION_PROPOSED110_01.json')
    assert pin(OLD/'EXTENSION_PROPOSED110_01.json')['sha256']=='d4fff47a3c8fedfed298c79cb1e0316a2d63cb47f0c378ff6fc04bc0aa5ec655'
    assert pin(OLD/'CUMULATIVE_ALLOCATION_PROPOSED110_01.json')['sha256']=='32a3870e0eb5f13c7910b8179a0b855aaf05ae2429d3df211b8246750299e7e3'
    assert len(extension['claims'])==59 and extension['consumed_before']==76 and extension['cumulative_ceiling']==110
    base=extension['base_family'];assert base['prior_attempts']==17 and base['attempt_budget']==51
    records=copy.deepcopy(extension['claims'])
    for name in ('eth-paper-real-data-end-to-end-resource-20261012-38','eth-paper-real-data-end-to-end-resource-20261012-39'):
        directory=ROOT/'research_runs'/name
        claim=load(directory/'claim.json');assert claim['family']==base and claim['effective_attempt_budget']==110
        records.append({'experiment':name,'claim_sha256':pin(directory/'claim.json')['sha256'],'terminal_sha256':pin(directory/'failed.json')['sha256'],'terminal_status':'failed'})
    seen=set();dispositions={'complete':0,'failed':0};latest=base['attempt_budget']
    for item in records:
        name=item['experiment'];assert name not in seen;seen.add(name);d=ROOT/'research_runs'/name
        cb=read(d/'claim.json');tb=read(d/(item['terminal_status']+'.json'));c=json.loads(cb);t=json.loads(tb)
        assert hashlib.sha256(cb).hexdigest()==item['claim_sha256'] and hashlib.sha256(tb).hexdigest()==item['terminal_sha256']
        assert c['experiment_id']==t['experiment_id']==name and c['program_id']==extension['program_id'] and c['family']==base
        assert t['claim_sha256']==item['claim_sha256'] and t['status']==item['terminal_status']
        assert not (d/({'complete':'failed.json','failed':'complete.json'}[item['terminal_status']])).exists()
        latest=max(latest,c.get('effective_attempt_budget',base['attempt_budget']));dispositions[item['terminal_status']]+=1
    assert len(records)==61 and latest==110 and dispositions=={'complete':20,'failed':41}
    actual=set()
    for d in (ROOT/'research_runs').iterdir():
        p=d/'claim.json'
        if not d.is_dir() or not p.is_file():continue
        c=load(p)
        if c.get('program_id')==extension['program_id'] and c.get('family')==base:actual.add(c['experiment_id'])
    assert actual==seen
    history_path=ROOT/'research/onchain-paper-replication-2026-09-24/history.json';history=load(history_path)
    assert history['prior_attempts']==17 and len(history['lineage'])==17
    for path,digest in history['metadata_hashes'].items():assert pin(ROOT/path)['sha256']==digest
    historical={'complete':0,'failed':0}
    for name in history['lineage']:
        d=ROOT/'research_runs'/name;found=[status for status in historical if (d/(status+'.json')).is_file()];assert len(found)==1
        status=found[0];c=load(d/'claim.json');t=load(d/(status+'.json'))
        assert c['experiment_id']==t['experiment_id']==name and t['claim_sha256']==pin(d/'claim.json')['sha256'] and t['status']==status
        historical[status]+=1
    assert historical=={'complete':13,'failed':4}
    assert all(not os.path.lexists(ROOT/'research_runs'/n) for n in NAMES)
    reason='PROPOSED_UNUSED. One fixed fresh resource identity40 after permanently FAILED39 pre-transport lease starvation. Preserve78spent (17historical+61actual), all110old allocations,28pending,3oldpreclaimreserved and unused37; no refund/transfer/reopen. Exact reviewed polling/byte-identical hashing/private weekly pin/two-worker historical claims/telemetry changes precede execution. Retain seven WHOLE graphs415968128cells and genuine GAT-attention-LSTM joint update/checkpoint. Original39 completed65536cell prefix can be carried only through independently accepted exact counter/no-tail and genuine recovered ancestry; missing proof refuses rather than recomputes or fabricates accounting. Same physical caps16GBhost/native6GiBmax5GiBhighswap0twoCPU8h/10GiBfloor; no cap ladder or financialfit65 allowance. Original32motifs512spent samples and fixed scientific protocol/tolerances unchanged. Actual final source/runtime/input/capacity/recovery/native eligibility and exact release required before ONE unused eligible claim.'
    allocation.update(status='PROPOSED_UNUSED',closed_claims=records,consumed_before=78,prior_adopted_cumulative_ceiling=110,prior_reviewed_reserved_ceiling=110,proposed_cumulative_ceiling=111,identities=NAMES,new_fixed_allocation={'full_seven_graph_joint_update_resource_pilot_claims':1},preserved_unused37={'identity':'eth-paper-real-data-end-to-end-resource-20261011-37','allowance':1,'status':'reserved_unavailable_dependency36_qualification_failed','claim':False},equation='111 =78permanently spent (17historical +61actualclosed) +28unchanged pending +3preserved closed preclaim reserved +1preserved unused37 +1fresh fixed resource claim',question='Measure improved genuine seven-whole-graph throughput/capacity and joint update while retaining authenticated completed-prefix ancestry.',qualification=reason)
    save('CUMULATIVE_ALLOCATION_PROPOSED111_01.json',allocation)
    extension.update(cumulative_ceiling=111,consumed_before=78,initial_experiment=NAMES[0],allocation=pin(HERE/'CUMULATIVE_ALLOCATION_PROPOSED111_01.json'),claims=records,reason=reason);save('EXTENSION_PROPOSED111_01.json',extension)
    save('ACTUAL_ACCOUNTING_READBACK01.json',{'status':'DRAFT_NOT_RELEASED','base_family':base,'actual_original_claims':61,'actual_dispositions':dispositions,'historical_prior_attempts':17,'historical_dispositions':historical,'historical_metadata':pin(history_path),'closed_cumulative':78,'cumulative_dispositions':{k:historical[k]+dispositions[k] for k in historical},'highest_actual_claim_ceiling':latest,'all_actual_same_family_claims_matched':True,'preserved_previous_allocation':pin(OLD/'CUMULATIVE_ALLOCATION_PROPOSED110_01.json'),'preserved_previous_extension':pin(OLD/'EXTENSION_PROPOSED110_01.json'),'unchanged_pending':28,'unchanged_preclaim_reserved':3,'preserved_unused37':1,'new_fixed':1,'proposed':111,'new_claim':False,'actual_raw_claim_terminal_checks':records})
    print(json.dumps({'actual_claims':61,'historical':17,'closed':78,'actual_dispositions':dispositions,'historical_dispositions':historical,'highest':latest,'proposed':111,'claim':False}))
if __name__=='__main__':main()
