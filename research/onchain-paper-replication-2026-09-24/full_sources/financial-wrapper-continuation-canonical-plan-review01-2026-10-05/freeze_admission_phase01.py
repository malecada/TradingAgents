"""Freeze a finite source/admission phase; later final authority stays additive."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;F=H.parent
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import R
def ref(name):return {'path':str(H/name),'sha256':R.digest(R.read(H,name))}
roles={'source_review':ref('SOURCE_MACHINE01.json'),'parent_review':ref('ADMISSION_PHASE_MACHINE01.json'),'source_input_runtime':ref('SOURCE_INPUT_RUNTIME_PROOF01.json'),'cumulative':ref('CUMULATIVE_PROOF01.json')}
R.put(H/'ADMISSION_PHASE_REFS01.json',{'schema_version':1,'roles':roles,'origin_root':str(H),'snapshot':'ADMISSION_PHASE_MANIFEST01.json plus precisely its listed members','future_recovery_and_final_authority_excluded':True,'scope':'Actual exact source correction, installed ten-body source-bound DRAFT Parent, independent metadata proofs, retained original builder witness and source-only literal installation release. Runtime and original recovery bases reused within their accepted historical scope; no native entry or public preflight grant.'})
m=R.scan(H);m['self_excluded']='ADMISSION_PHASE_MANIFEST01.json';m['scope']='Immutable finite source/admission snapshot within an open consolidated review. Later actual recovery/final authority files are outside this snapshot.';R.put(H/'ADMISSION_PHASE_MANIFEST01.json',m)
print(json.dumps({'manifest':ref('ADMISSION_PHASE_MANIFEST01.json'),'mapping':ref('ADMISSION_PHASE_REFS01.json'),'roles':roles,'members':len(m['members'])}))
