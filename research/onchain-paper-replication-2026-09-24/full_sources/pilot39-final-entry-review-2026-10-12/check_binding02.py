"""Changed binding refs only; reuse prior exact source/input review."""
import hashlib,json,stat
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];F=D.parent;E=F/'real-data-pilot-full39-entry-preparation01-2026-10-12';checks=[]
def pin(p):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and not p.is_symlink();b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(p.read_bytes())
def ck(n,v):assert v,n;checks.append(n)
a=load(E/'BINDING_DRAFT01.json');b=load(E/'BINDING_SUBMITTED01.json');old=load(D/'BINDING_REVIEW01.json')
ck('exact actual submittedbody',pin(E/'BINDING_SUBMITTED01.json')['sha256']=='fad7bd61067f26a702ca511528a2bbc32a6011b5c4879cddbdd402125b19e6b8')
ck('onlytwoactualrecoveryrefsandstatus',set(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k))=={'complete_increment_recovery','new_increment_recovery_review','status'})
ck('previous exact review',pin(D/'BINDING_REVIEW01.json')['sha256']=='35de7dc2675e1e3e0dbc5706800035e7d804124b294a0b5a640061e135763abd')
for role in ('complete_increment_recovery','new_increment_recovery_review'):ck('genuine '+role,pin(R/b[role]['path'])==b[role])
rv=load(R/b['new_increment_recovery_review']['path']);rec=load(R/b['complete_increment_recovery']['path'])
ck('independent accepted36 exactreceiptjoin',rv['decision']=='accepted' and pin(R/b['new_increment_recovery_review']['path'])['sha256']=='418b1f34159a7cfef13eec3222e12027c6fb86d32e535c6a3e2f1b7756bb7043' and rv['evidence'][b['complete_increment_recovery']['path']]==b['complete_increment_recovery']['sha256'])
ck('actual36scopeandsource',rv['source']==rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']=='28f04c1b7fb936f3f94b085a0fc01d0f0a353519' and rv['operation_count']==13 and rv['regular_files']==150 and rv['directories']==18 and rv['archive']==rec['returned_archive'] and rv['gate_source_pins']==1142 and rv['input_roles']==73 and rv['final_binding_release_recovered'] is False)
# Current small exact bodies only; source1142/input73 check is reused without rerunning it.
for n in ('gate01.json','preflight39_01.py','root_io39_01.py','BINDING_DRAFT01.json','CORE_MANIFEST01.json','CAPACITY_DECLARATION_ROOT01.json'):
 p=E/n;v=pin(p);ck('unchanged current concrete '+n,old['evidence'][v['path']]==v['sha256'])
nulls=sorted(k for k,v in b.items() if v is None);ck('onlybindingreviewandunusednulls',nulls==['binding_readback','binding_review','endpoint_review'])
ck('exactpriorrosterandidentity',b['identity']==old['identity'] and b['input_refs']==old['input_refs'] and len(old['input_refs'])==73)
out={k:v for k,v in old.items() if k!='checks'};out['checks']=checks;out['scope']='Actual whole39 submitted binding with genuine increment36 recovery; prior1142source/73input exact checks reused. Final Binding01 and final release still pending.';out['evidence']=dict(old['evidence']);out['unavailable_binding_roles']=nulls
for p in (D/'BINDING_REVIEW01.json',E/'BINDING_SUBMITTED01.json',R/b['complete_increment_recovery']['path'],R/b['new_increment_recovery_review']['path']):v=pin(p);out['evidence'][v['path']]=v['sha256']
out['limitations']=['No re-execution of source/input matrix, helpers/admission/scans/numerics/Owner/claim/Git/network.','Final Binding01 is not yet created or released; this review is outside archive36 by explicit cycle handling.','Binding readback/endpoint review remain literal null optional navigation; binding_review is the sole required missing binding role and must point to this actual review.','Prospective guarded storage only; full memory fit/physical reservation remain unproved.']
with (D/'BINDING_REVIEW02.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':len(checks),'review':pin(D/'BINDING_REVIEW02.json')}))
