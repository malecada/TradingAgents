from pathlib import Path
import copy,hashlib,importlib.util,json
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('metadata_prepare',H/'prepare01.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
r=p.r
j=json.loads((H/'INVERSE01.json').read_text());source=(H/'retire01.py').read_text();rev=source
for e in reversed(j['edits']):
    if e['after']:
        assert rev.count(e['after'])==1
        rev=rev.replace(e['after'],e['before'],1)
    else:rev=rev.replace('    recovery(ROOT,c)\n','    recovery(ROOT,c)\n'+e['before'],1)
assert rev==(r.ROOT/j['baseline']).read_text()
assert hashlib.sha256(source.encode()).hexdigest()==j['candidate_sha256']
draft=p.prepare(); refused=[]
def refusal(label,fn):
    try:fn()
    except (ValueError,KeyError,TypeError):refused.append(label)
    else:raise AssertionError(label+' did not refuse')
refusal('null independent outcome review',lambda:r.recovery(r.ROOT,draft))
bad=copy.deepcopy(draft);bad['rows'][0]['recovered']['path']=bad['rows'][0]['original']['path']
refusal('original payload cannot be selected for deletion',lambda:r.selected(r.ROOT,bad))
bad=copy.deepcopy(draft);bad['rows'][0]['index']=11
refusal('old complete-graph ledger index refuses',lambda:r.selected(r.ROOT,bad))
review='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph-failed-preservation-outcome-review01-2026-10-06/REVIEW01.json'
sha='c6edefef9784b60ea8ad1ba331f0d12e7f6dea9add644517969f0800fc68a785'
actual=p.prepare(review,sha)
assert actual['status']=='DRAFT_NOT_RELEASED' and actual['release'] is None
r.selected(r.ROOT,actual)
result={'decision':'pass','exact_inverse':True,'refusals':refused,'actual_bounded_recovery_join_pass':True,'actual_review':{'path':review,'sha256':sha},'selected_originals_and_gets_current_stat_only':3,'retire_bytes':3278655680,'payload_reads_or_hashes':0,'inactive_systemctl_not_called':True,'execute_not_called':True,'release_created':False}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
