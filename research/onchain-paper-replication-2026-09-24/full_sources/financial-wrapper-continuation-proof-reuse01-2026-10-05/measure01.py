"""Measure real draft four-definition/reused-proof read set with unchanged Reader.
This byte probe does not run the public validator, create an Admission or confer authority.
"""
from pathlib import Path
import json,hashlib,importlib.util
H=Path(__file__).resolve().parent;B=H.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01';sha=lambda b:hashlib.sha256(b).hexdigest();s=importlib.util.spec_from_file_location('_measured_proof_reuse',H/'preclaim_reuse01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
old=json.loads((B/'financial-wrapper-continuation-preclaim-budget-implementation01-2026-10-05/KNOWN_LAYOUT_READ_SET01.json').read_text());rows={x['path']:x for x in old['rows']};oldmachine=json.loads(Path(m.REUSE_EXTERNAL['recovery_machine']['path']).read_text());remove={x['path'] for x in list(m.REUSE_EXTERNAL.values())+oldmachine['recovery_receipts']};removed=[]
for p in remove:
 if p in rows:removed.append(rows.pop(p))
# Replace obsolete draft scenario bodies only; preserve each required role's bytes.
for p in [CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json',P/'preclaim01.py',CAP/'fixture_inputs/financial_wrapper_compatibility01/wrapper_plan.json']:
 rows.pop(str(p),None)
for x in list(rows.values()):
 if x['path'].endswith('/PRIOR_DESCRIPTOR_DRAFT01.json') or x['path'].endswith('/REFERENCE_DESCRIPTOR_DRAFT01.json'):rows.pop(x['path'])
paths=[H/'GATE4_DRAFT01.json',H/'preclaim_reuse01.py',H/'PROOF_REUSE_CONTRACT_DRAFT01.json',H/'inputs/continue-plan.json',H/'inputs/prior.json',H/'inputs/reference.json']+[Path(x['path']) for x in m.REUSE_ANCHORS.values()]+[Path(m.REUSE_EXTERNAL[k]['path']) for k in ('review_proof','recovery_proof','review_machine','review_report')]
for p in paths:
 b=p.read_bytes();rows[str(p)]={'path':str(p),'bytes':len(b),'sha256':sha(b),'category':'exact_new_draft_or_known_immutable_proof_root'}
r=m.Reader()
for x in rows.values():b=r.read(Path(x['path']));assert len(b)==x['bytes'] and sha(b)==x['sha256']
first=r.total;r.finish();assert r.total==first*2
out={'schema_version':1,'status':'ACTUAL_DRAFT_READ_SET_FITS_NOT_FULL_ADMISSION','unique_paths':len(rows),'first_bytes':first,'including_finish_bytes':r.total,'remaining_charged_bytes':m.TOTAL-r.total,'remaining_unique_bytes_if_read_twice':(m.TOTAL-r.total)//2,'old_gate_untouched':True,'old_external_raw_bodies_retained_and_replaced_by_fixed_proof_ancestry':len(removed),'new_gate_bytes':(H/'GATE4_DRAFT01.json').stat().st_size,'future_unknowns':['actual new current/design source/gate pins','registered prediction output descriptors unavailable until continuation','actual Root final Parent/helpers/contract and three current proof byte deltas','actual completed100 outcome recovery proof and independent review bytes','actual Root-pinned reuse contract binding in source runtime proof','full public Admission/preclaim/native checks'],'full_public_validator_executed':False,'new_complete100_recovery_proof_available':False,'numerical_authority':False,'inventory':list(rows.values()),'replaced_raw_ancestry_refs':removed}
(H/'MEASURED_READ_SET01.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','replaced_raw_ancestry_refs']}))
