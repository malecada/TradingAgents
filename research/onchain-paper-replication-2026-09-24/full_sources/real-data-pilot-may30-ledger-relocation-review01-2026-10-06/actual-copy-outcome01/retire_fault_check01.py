"""Synthetic fault injection into the real RETIRE body; no genuine authority constructed."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,types
from unittest.mock import patch
H=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-may30-ledger-relocation-retire-disposition02-2026-10-06'); REVIEW=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retire_candidate',H/'relocate01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
inv=json.loads((H/'INVERSE01.json').read_text());text=(H/'relocate01.py').read_text();back=text
for e in reversed(inv['edits']):
    assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
assert back==(m.ROOT/inv['baseline']).read_text()
a=ast.parse(back);b=ast.parse(text)
assert [ast.dump(n) for n in a.body if not isinstance(n,ast.FunctionDef) or n.name!='retire']==[ast.dump(n) for n in b.body if not isinstance(n,ast.FunctionDef) or n.name!='retire']
assert hashlib.sha256((H/'entry01.py').read_bytes()).hexdigest()==inv['entry_sha256_unchanged']
fixture=REVIEW/'synthetic01';fixture.mkdir(exist_ok=False);results=[]
for kind in ('post-unlink-sync','uncertain-unlink','bridge-publication'):
    root=fixture/kind;root.mkdir();here=root/'receipts';here.mkdir();store=root/'Data';store.mkdir();dst=store/'ledger.sqlite';dst.write_bytes(b'ledger');src=root/'original.sqlite';src.write_bytes(b'ledger');s=src.stat()
    row={'path':'original.sqlite','bytes':6,'sha256':hashlib.sha256(b'ledger').hexdigest(),'mode':s.st_mode&0o777,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
    target={'path':str(dst),'device':dst.stat().st_dev,'bytes':6,'sha256':row['sha256'],'stat_identity':m.sig(dst.stat())}
    cref={'path':'copy.json','sha256':'c'*64};rref={'path':'review.json','sha256':'d'*64}
    bodies={'copy.json':{'identity':m.ID,'original':row,'target':target,'copy_readback_verified':True,'original_retired':False,'typed_name_mode_verified':True,'original_claim_sha256':'claim','original_source':'source'},'review.json':{'decision':'accepted','identity':m.ID,'copy_receipt_sha256':'c'*64,'full_destination_readback_verified':True}}
    fake=types.SimpleNamespace(inactive=lambda:None,metadata=lambda root,path,pin:json.dumps(bodies[path]).encode(),identity=lambda s:[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns],current=lambda root,row:root/row['path'])
    c={'target':{k:target[k] for k in ('path','device','bytes','sha256')},'recovery_selection':{'rows':[{'original':row}]}}
    release={'decision':'accepted','phase':'retire','identity':m.ID,'copy_receipt':cref,'copy_review':rref}
    original_publish=m.publish;original_unlink=Path.unlink;seen=[]
    class Fault(RuntimeError):pass
    problem=Fault(kind)
    def publish(path,value):
        if kind=='bridge-publication' and path.name=='relocation-receipt01.json':raise problem
        original_publish(path,value)
    def sync(path):
        # Receipt fsyncs remain real; fail only after the original unlink.
        if kind=='post-unlink-sync' and path==root:raise problem
    def unlink(path,*args,**kwargs):
        original_unlink(path,*args,**kwargs)
        if kind=='uncertain-unlink' and path==src:raise problem
    with patch.object(m,'ROOT',root),patch.object(m,'TARGET',dst),patch.object(m,'validate',lambda c:(fake,row)),patch.object(m,'room',lambda c:None),patch.object(m,'syncdir',sync),patch.object(m,'publish',publish),patch.object(Path,'unlink',unlink):
        try:m.retire(root,here,c,release)
        except Fault as error:assert error is problem
        else:raise AssertionError('fault not propagated')
    failed=json.loads((here/'retire-failed01.json').read_text());assert failed['unlink_attempted']==['original.sqlite'] and dst.read_bytes()==b'ledger' and not src.exists()
    if kind=='uncertain-unlink':assert failed['removed']==[] and failed['ambiguous_attempts']==['original.sqlite'] and failed['source_retired'] is None and failed['stage']=='unlink-original'
    else:assert failed['removed']==['original.sqlite'] and failed['ambiguous_attempts']==[] and failed['source_retired'] is True
    assert not (here/'relocation-receipt01.json').exists()
    results.append({'fault':kind,'stage':failed['stage'],'source_retired':failed['source_retired'],'removed':failed['removed'],'ambiguous_attempts':failed['ambiguous_attempts'],'original_exception_preserved':True})
result={'decision':'pass','exact_literal_inverse':True,'all_AST_outside_retire_unchanged':True,'entry_byte_unchanged':True,'synthetic_actual_retire_body_faults':results,'real_payload_reads_or_unlinks':0,'genuine_authority_constructed':False,'close_fault_not_separately_injected':'Same catch preserves recorded lists; actual close path reviewed statically.'}
(REVIEW/'RETIRE_FAULT_CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
