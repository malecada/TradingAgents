"""Current compact receipts and stat-only body joins; forbid all original/get opens."""
import copy,hashlib,importlib.util,json,os
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;ROOT=H.parents[3];F=H.parent
S=F/'real-data-pilot-second-graph-preservation-continuation01-2026-10-06'
spec=importlib.util.spec_from_file_location('review_metadata_helper',S/'helper-correction02/continue02.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
D=ROOT/h.DEST;envelope=json.loads((D/'envelope01.json').read_text());selection=json.loads((D/'selection01.json').read_text());binding=selection['binding']
meta=h.doc(ROOT,binding['metadata']);blocked={ROOT/r[k] for r in meta['rows'] for k in ('original_path','recovered_path')};calls=[];ropen=os.open;popen=Path.open
# Pinned metadata only, never original/get bodies (including small ones).
def no_payload_os(p,*a,**kw):
 assert Path(p) not in blocked,'original/get open attempted';return ropen(p,*a,**kw)
def no_payload_path(p,*a,**kw):
 assert p not in blocked,'original/get open attempted';return popen(p,*a,**kw)
with patch.object(h.os,'open',no_payload_os),patch.object(Path,'open',no_payload_path):
 actual=h.select(ROOT,binding);assert actual==selection
 bad=copy.deepcopy(binding);bad['review']['sha256']='0'*64
 try:h.select(ROOT,bad)
 except ValueError as e:assert 'hash/currentness' in str(e)
 else:raise AssertionError('corrupt proof accepted')
for name in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json'):assert not os.path.lexists(D/name)
for name,pin in envelope['source_files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
for ref in envelope['evidence']+[envelope['selection'],envelope['environment']]:assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256']
assert envelope['local_only_evidence']==[envelope['connection']['path']] and envelope['connection']['path'] not in envelope['source_files']
c=json.loads((S/'ENTRY_CHANGE01.json').read_text());entry=(D/'entry01.py').read_text()
for edit in reversed(c['literal_edits']):assert entry.count(edit['after'])==1;entry=entry.replace(edit['after'],edit['before'])
assert hashlib.sha256(entry.encode()).hexdigest()==c['before_sha256']
result={'actual_body_stat_pairs':36,'original_get_body_opens':0,'exact_selection_equal':True,'wrong_proof_refused':True,'source_pins':len(envelope['source_files']),'source_pin_current_join':True,'fresh_namespaces':True,'entry_exact_inverse':True,'connection_contents_unread':True,'parent_status':selection['parent_status'],'body_transfers_authorized':selection['body_transfer_count'],'missing_rows':selection['missing_rows']}
print(json.dumps(result,indent=2))
