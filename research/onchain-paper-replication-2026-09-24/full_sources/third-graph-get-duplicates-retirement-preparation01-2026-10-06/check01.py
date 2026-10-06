"""One focused inverse/null/changed-recovery predicate check; no real authority."""
from pathlib import Path
import copy,hashlib,json
H=Path(__file__).resolve().parent;M=H.parents[3]
s=(H/'retire01.py').read_text();delta=json.loads((H/'INVERSE01.json').read_bytes());inverse=s
for e in reversed(delta['literal_edits']):
    assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'])
assert inverse.encode()==(M/delta['baseline']).read_bytes()
env={'__file__':str(H/'retire01.py'),'__name__':'offline_check'};exec(compile(s,str(H/'retire01.py'),'exec'),env)
template=json.loads((H/'SELECTION_TEMPLATE01.json').read_bytes())
try:env['recovery'](M,template)
except ValueError as e:assert 'actual exact recovery ref' in str(e)
else:raise AssertionError('null future evidence accepted')
release=H/'RELEASE_TEMPLATE01.json'
try:env['execute'](release,hashlib.sha256(release.read_bytes()).hexdigest())
except ValueError as e:assert 'exact independent release' in str(e)
else:raise AssertionError('null release accepted')
assert not any((H/n).exists() for n in ['attempt01.json','complete01.json','failed01.json'])
# In-memory synthetic recovery objects exercise new predicates only. No files,
# ResearchRun, Owner, native process, original/get descriptor or deletion is used.
backup=env['BACKUP'];expectedentry='87cbe18ecb421b5850e3cbed8a4f5d3f9516b2129d3d0cc034197c9f5f6ff035'
entrypath='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-third-graph-post-recovery-retirement-preparation01-2026-10-06/retire01.py'
entryraw=(M/entrypath).read_bytes();assert hashlib.sha256(entryraw).hexdigest()==expectedentry
def check(failure=None):
    rows=[{'index':i,'kept':f'kept-{i}.json'} for i in [21,22,23,25,26]]
    complete={'identity':Path(backup).name,'count':36,'files':[{'index':i} for i in range(36)],'originals_retained':True,'recoveries_retained':True}
    data={backup+'/complete.json':complete,backup+'/recovered-complete.json':copy.deepcopy(complete),backup+'/guard01/final.json':{},backup+'/outer-exit01.json':{},backup+'/ROOT_TERMINAL01.json':{'actual_root_tool_exit_code':0}}
    for row in rows:data[row['kept']]=complete['files'][row['index']]
    removed=['synthetic-ledger','synthetic-get']
    data['retired.json']={'identity':'real-pilot-third-graph-ledger-retirement-20261006-01','preservation_backup':Path(backup).name,'payload_bytes_retired':6621847552,'arrays_retained':True,'removed':removed}
    if failure=='root1':data[backup+'/ROOT_TERMINAL01.json']['actual_root_tool_exit_code']=1
    raw={k:json.dumps(v).encode() for k,v in data.items()};pins={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    data['ledger-root.json']={'actual_root_exit_code':1 if failure=='ledger-root1' else 0,'complete_sha256':pins['retired.json']}
    data['outcome.json']={'decision':'accepted','identity':Path(backup).name,'full_scope_byte_recovery':failure!='no-full-scope','evidence':dict(pins)}
    for k in ['ledger-root.json','outcome.json']:raw[k]=json.dumps(data[k]).encode();pins[k]=hashlib.sha256(raw[k]).hexdigest()
    raw[entrypath]=entryraw;pins[entrypath]=expectedentry
    c={'rows':rows,'removed_ledger_paths':removed,'evidence':pins,'recovery_basis':{k:{'path':p,'sha256':pins[p]} for k,p in [('outcome_review','outcome.json'),('ledger_complete','retired.json'),('ledger_root','ledger-root.json'),('ledger_entry',entrypath)]}}
    def metadata(root,p,pin=None):
        assert hashlib.sha256(raw[p]).hexdigest()==pin;return raw[p]
    env['metadata']=metadata;env['recovery'](Path('/synthetic'),c)
check();refusals=[]
for case in ['root1','ledger-root1','no-full-scope']:
    try:check(case)
    except ValueError as e:refusals.append({'case':case,'refusal':str(e)})
    else:raise AssertionError(case)
result={'decision':'pass-source-only','exact_inverse':True,'null_selection_and_release_refused':True,'synthetic_valid_recovery_gate':True,'refusals':refusals,'future_actual_scope_observed':False,'native_network_deletion_claim_payload_reads':0,'note':'Inherited native/descriptor/lock/stat/active-consumer/error logic is unchanged by exact inverse. In-memory predicate fixtures are not release evidence.'}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
