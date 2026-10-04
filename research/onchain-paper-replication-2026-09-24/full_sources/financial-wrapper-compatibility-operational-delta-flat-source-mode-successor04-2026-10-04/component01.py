from pathlib import Path
import importlib.util,json,hashlib,sys,traceback,stat,os
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));I=D.parent/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load('mode_old',D/'ORIGINAL_restore01.py');M=load('mode_new',D/'restore01.py');raw=(I/'REMOTE_RECOVERY01.json').read_bytes();remote=json.loads(raw);selection_raw=(I/'SELECTED_BODIES01.json').read_bytes();selection=json.loads(selection_raw);pin=H(selection_raw);rows=[]
def snapshot():
 return [(str(p.relative_to(I/'selected')),tuple(getattr(p.lstat(),k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_size','st_mtime_ns','st_ctime_ns'))) for p in [I/'selected',*sorted((I/'selected').rglob('*'))]]
before=snapshot()
try:O.authenticate_selected(I,remote,selection,pin)
except ValueError as e:rows.append({'source':'original03','result':'RED','error':str(e),'traceback':traceback.format_exc()});assert str(e)=='cohort root private owner/mode'
else:raise AssertionError('old component unexpectedly accepts actual775')
cohort=M.VerifiedCohort();records=M.authenticate_selected(I,remote,selection,pin,cohort);cohort.check();assert len(records)==15 and sum(x['bytes'] for x in records)==507946
rows.append({'source':'candidate04','result':'GREEN_READ_ONLY_COMPONENT','records':len(records),'logical_bytes':sum(x['bytes'] for x in records),'cohort_pins':len(cohort.pins),'actual_byte_proofs':len(cohort.byte_proofs),'tree_roots':[str(x) for x in cohort.trees],'anchors':len(cohort.anchors),'original_modes_bound':cohort.selected_profile['directory_modes']})
assert before==snapshot();assert (I/'REMOTE_RECOVERY01.json').read_bytes()==raw and (I/'SELECTED_BODIES01.json').read_bytes()==selection_raw
(D/'COMPONENT01.json').write_text(json.dumps({'source_sha256':H((D/'restore01.py').read_bytes()),'actual_remote_sha256':H(raw),'selection_sha256':pin,'rows':rows,'original_selected_full_signatures_unchanged':True,'original_input_modes_unchanged':True,'actual_restoration_or_entry':False,'created_accepted_authority':False},indent=2)+'\n');print(json.dumps(rows))
