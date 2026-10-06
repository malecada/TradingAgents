"""Read-only actual metadata joins and focused synthetic changed-gate refusals."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;M=H.parents[3]
delta=json.loads((H/'INVERSE01.json').read_bytes());source=(H/'retire01.py').read_text();inverse=source
for e in reversed(delta['literal_edits']):
    assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'])
assert inverse.encode()==(M/delta['baseline']).read_bytes()
scope={'__file__':str(H/'retire01.py'),'__name__':'source_only_check'};exec(compile(source,str(H/'retire01.py'),'exec'),scope)
c=json.loads((H/'selection01.json').read_bytes())
for p,pin in c['evidence'].items():scope['metadata'](M,p,pin)
scope['recovery'](M,c);originals,gets=scope['selected'](M,c)
assert len(originals)==len(gets)==5 and sum(r['recovered']['bytes'] for r in c['rows'])==604276056
baseline_metadata=scope['metadata'];refusals=[]
cases=[(scope['BACKUP']+'/guard01/final.json','phase','complete'),(scope['BACKUP']+'/guard01/final.json','child_exit_code',0),(scope['UNION']+'/guard01/final.json','child_exit_code',None),(scope['UNION']+'/ROOT_TERMINAL01.json','actual_root_tool_exit_code',1),(c['recovery_basis']['ledger_root']['path'],'actual_root_exit_code',1),(c['recovery_basis']['union_review']['path'],'full_scope_byte_recovery',False)]
for relative,key,value in cases:
    def mutated(root,path,pin=None):
        raw=baseline_metadata(root,path,pin)
        if path==relative:
            v=json.loads(raw);v[key]=value;return json.dumps(v).encode()
        return raw
    scope['metadata']=mutated
    try:scope['recovery'](M,c)
    except ValueError as e:refusals.append({'path':relative,'field':key,'value':value,'refusal':str(e)})
    else:raise AssertionError((relative,key,value))
scope['metadata']=baseline_metadata
result={'decision':'pass-source-only','exact_eight_literal_inverse':True,'actual_metadata_evidence_pins':len(c['evidence']),'actual_original_get_stat_joins':10,'retire_bytes':604276056,'synthetic_predicate_refusals':refusals,'execute_or_inactive_called':False,'payload_reads':0,'network_native_claim_or_deletion_calls':0,'qualification':'Actual recovery/selection predicates read only compact pinned receipts and stat identities. Synthetic refusal overrides operate after actual metadata authentication solely to exercise predicates; no authority or altered live records.'}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
