"""Source-only fixed identity preparation. No selection/transport/native execution."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OLD_ID='real-pilot-sixth-graph-preservation-20261006-01'
ID='real-pilot-july25-ledger-preservation-20261006-01'
BASE=ROOT/'research/onchain-paper-replication-2026-09-24'
OLD_HELPER=BASE/'full_sources/real-data-pilot-june6-preservation-preparation01-2026-10-06/keep.py'
OLD_ENTRY=BASE/'storage'/OLD_ID/'entry01.py'
OLD_ENVELOPE=OLD_ENTRY.with_name('envelope01.json')
FUTURE=BASE/'storage'/ID
LEDGER='research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-07-25/decode_graph/weekly-g_35n27n/events.sqlite'
GIB=1024**3

def raw(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def ref(path):return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def need(ok,message):
    if not ok:raise ValueError(message)

def prepare():
    need(ref(OLD_HELPER)['sha256']=='6a751544e523bfc3b802a6fda15c96c7bdeee1d00f2e12b5457fd4fa652ff5ad','accepted June6 helper changed')
    need(ref(OLD_ENTRY)['sha256']=='ffa5092f4f03aebc24391ab5f373f741ad7706b9fd472bbac3adda81bce23f07','accepted actual June6 entry changed')
    inverse={};delta=[]
    for original,name in ((OLD_HELPER,'keep.py'),(OLD_ENTRY,'entry01.py')):
        before=original.read_text();need(before.count(OLD_ID)==1,'fixed identity occurrence differs')
        after=before.replace(OLD_ID,ID);(HERE/name).write_text(after);compile(after,str(HERE/name),'exec')
        reversed_text=after.replace(ID,OLD_ID)
        need(reversed_text==before and ast.dump(ast.parse(reversed_text))==ast.dump(ast.parse(before)),'literal/AST inverse differs')
        inverse[name]={'before':ref(original),'candidate':ref(HERE/name),'identity_substitutions':1,'literal_inverse_equal':True,'ast_inverse_equal':True}
        delta.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+str(original.relative_to(ROOT)),tofile='b/'+str((HERE/name).relative_to(ROOT))))
    # Read only the existing non-secret envelope. Never dereference connection.
    old=json.loads(OLD_ENVELOPE.read_text());envelope=copy.deepcopy(old)
    need(old['identity']==OLD_ID and old['connection']['path'] not in old['source_files'],'accepted envelope identity/private exclusion differs')
    envelope['identity']=ID;envelope['selection']=None;envelope['evidence']=[None]
    old_helper=old['helper']['path'];old_entry=str(OLD_ENTRY.relative_to(ROOT))
    need(old_helper in envelope['source_files'] and old_entry in envelope['source_files'],'exact old helper/entry source pins absent')
    del envelope['source_files'][old_helper];del envelope['source_files'][old_entry]
    envelope['helper']=ref(HERE/'keep.py');envelope['source_files'][envelope['helper']['path']]=envelope['helper']['sha256']
    pins={}
    for path in tuple(envelope['source_files']):
        need(path.endswith('.py'),'source-only pin expected')
        current=ref(ROOT/path);pins[path]={'inherited_sha256':old['source_files'].get(path),'current_sha256':current['sha256']};envelope['source_files'][path]=current['sha256']
    # This path is prospective. Root copies exact entry bytes after independent
    # review and then binds actual committed source; no existence is invented.
    target_entry=str((FUTURE/'entry01.py').relative_to(ROOT));entry_sha=ref(HERE/'entry01.py')['sha256']
    envelope['source_files'][target_entry]=entry_sha
    envelope['scanner_sha256']=envelope['source_files']['tradingagents/research/onchain_replication/workflow_storage.py']
    need(envelope['source_files']['tradingagents/research/onchain_replication/resources.py']=='672ff3ed96c7d5ba1ccbdc2355558b10aa823cbda0c3b07d1d2f44923c8b0185','accepted current resources differs')
    need(envelope['scanner_sha256']=='deff02766685c1e7fb8628766acf0e0c36dc324da4672f3adc094bfac3e24a74','accepted current workflow storage differs')
    envelope['status']='UNBOUND_TEMPLATE_NOT_RELEASED'
    envelope['qualification']='Source-only one-ledger July25 preservation template. selection and historical closed-source evidence are intentionally null; independent actual release absent. Prospective entry path does not assert file existence. Current source pins are observations, not release. Originals and recoveries remain retained; no deletion or old-run restart authority.'
    need(envelope['connection']==old['connection'] and envelope['local_only_evidence']==old['local_only_evidence'],'opaque private reference changed')
    (HERE/'ENVELOPE_TEMPLATE01.json').write_bytes(raw(envelope))
    selection={'schema_version':1,'status':'UNBOUND_SINGLE_LEDGER_TEMPLATE_NOT_RELEASED','identity':ID,'files':[{'path':LEDGER,'bytes':None,'sha256':None,'stat_identity':None}],'count':1,'total_bytes':None,'max_body_bytes':None,'disk_floor_bytes':10*GIB,'transport_payload_budget_bytes':8*GIB,'owned_tree_limit_bytes':5*GIB,'remote':None,'qualification':'Only the named historical ledger is eligible for Root current stat/hash/closed-history binding. Reported3755212800B is not current stat evidence. No graph arrays, labels, model/dictionary or claim files are selected.'}
    (HERE/'SELECTION_TEMPLATE01.json').write_bytes(raw(selection))
    (HERE/'INVERSE01.json').write_bytes(raw({'status':'SOURCE_ONLY_NOT_ADMITTED','files':inverse,'helper_path_change':'envelope helper and source-files key only; no helper path is embedded in accepted entry source'}))
    (HERE/'SOURCE_PINS01.json').write_bytes(raw({'base_envelope':ref(OLD_ENVELOPE),'original_helper':ref(OLD_HELPER),'original_actual_entry':ref(OLD_ENTRY),'current_source_observations':pins,'candidate_entry':ref(HERE/'entry01.py'),'prospective_entry_path':target_entry,'prospective_entry_exists_claimed':False,'private_connection_ref_copied_only':True,'private_connection_body_read':False}))
    (HERE/'BINDING_REQUIREMENTS01.json').write_bytes(raw({'identity':ID,'selected_path_only':LEDGER,'reported_bytes_not_stat_evidence':3755212800,'historical_closed_audit_ref':None,'current_stat_sha_selection_ref':None,'actual_independent_release_ref':None,'actual_committed_head':None,'actual_remote_head':None,'resources_unchanged':{'memory_max_bytes':256*1024**2,'memory_high_bytes':192*1024**2,'memory_swap_max_bytes':0,'reserve_bytes':3*GIB,'start_reserve_bytes':int(3.5*GIB),'cpus':2,'wall_seconds':14400,'owned_tree_bytes':5*GIB,'transport_payload_budget_bytes':8*GIB,'disk_floor_bytes':10*GIB,'entries':4096,'depth':16,'scan_seconds':5},'root_actions':['Bind exact closed historical audit and current single-ledger stat/SHA selection; preserve all historical dispositions.','Confirm exact helper/entry/current resource source pins, runtime inventory, private connection through existing protected handling.','Bind selection/evidence/envelope and independently reviewed release, commit/push/readback actual sources; verify one-use namespace and no active competing worker.','Perform exactly one separately released ordinary preservation launch. No deletion follows without actual full external recovery and a separate exact release.']}))
    (HERE/'DELTA01.patch').write_text(''.join(delta))
if __name__=='__main__':prepare()
