from pathlib import Path
import ast,hashlib,json,os,stat,time
H=Path(__file__).resolve().parent;B=H.parent;start=time.monotonic();facts=[];reads={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p,pin=None):
 p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
 b=p.read_bytes();sig=lambda t:(t.st_dev,t.st_ino,t.st_mode,t.st_nlink,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 assert sig(s)==sig(p.lstat()) and (pin is None or sha(b)==pin);reads[str(p)]={'path':str(p),'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(s.st_mode)};assert sum(x['bytes'] for x in reads.values())<=64*1024**2 and time.monotonic()-start<120;return b
def j(p,pin=None):return json.loads(read(p,pin))
def save(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
P=B/'financial-wrapper-compatibility-gate-preview02-2026-10-04';preview=j(P/'PREVIEW01.json');gatepath=P/preview['new_gate_path'];gate=j(gatepath,'e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806');identity=preview['identity'];exp=gate['experiments'][identity];CAP=Path(preview['root']);assert exp['parent'] is None and len(exp['inputs'])==11 and len(exp['source_files'])==354
policy=j(P/exp['inputs']['operational_source_compatibility']['path']);S=B/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04';source=read(S/'preclaim01.py','557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16');V=B/'financial-wrapper-compatibility-composed-recovery-review02-2026-10-04';PV=B/'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04';R=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01')
inputs=[];target=[]
for role,x in exp['inputs'].items():
 b=read(P/x['path'],x['sha256']);inputs.append({'role':role,'actual_preview_path':str(P/x['path']),'future_source_path':str(CAP/x['path']),'bytes':len(b),'sha256':sha(b),'first_read_count':1,'final_reread_count':1})
for p,h in policy['target']['installed'].items():
 b=read(CAP/p,h);target.append({'role':'target_implementation','path':str(CAP/p),'bytes':len(b),'sha256':h,'first_read_count':1,'final_reread_count':1})
assert len(target)==195
proofs={};external=[]
for kind,root,names in [('review',PV,['REVIEW_PROOF01.json','MACHINE01.json','MANIFEST01.json','REPORT01.md']),('recovery',V,['RECOVERY_PROOF01.json','MACHINE01.json','MANIFEST01.json','REPORT01.md'])]:
 for suffix,name in zip(['proof','machine','manifest','report'],names):
  b=read(root/name);proofs[kind+'_'+suffix]={'path':str(root/name),'sha256':sha(b)};external.append({'role':kind+'_'+suffix,'path':str(root/name),'bytes':len(b),'sha256':sha(b)})
recovery=j(V/'MACHINE01.json');receipts=[]
for ref in recovery['recovery_receipts']:
 b=read(Path(ref['path']),ref['sha256']);receipts.append({'role':'actual_recovery_receipt','path':ref['path'],'sha256':ref['sha256'],'bytes':len(b)})
helpers=[]
for n in ['supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json']:
 b=read(R/n);helpers.append({'name':n,'original_path':str(R/n),'sha256':sha(b),'bytes':len(b),'future_parent_path':None,'byte_change_required':False})
parent=read(R/'parent01.py');oldrequest=read(R/'REQUEST_DRAFT01.json');helpers.append({'name':'preclaim01.py','original_path':str(S/'preclaim01.py'),'sha256':sha(source),'bytes':len(source),'future_parent_path':None,'byte_change_required':False})
# Count cache by canonical PATH, never by content. Reader.finish charges each
# cached path's full physical read once again; signature rejoin charges no bytes.
known=inputs+target+[{'role':'registration','path':str(gatepath),'bytes':len(read(gatepath))}]+external+receipts+[{'role':'parent_helper','path':x['original_path'],'bytes':x['bytes']} for x in helpers]
assert len({x.get('path',x.get('actual_preview_path')) for x in known})==len(known)
known_bytes=sum(x['bytes'] for x in known);charged=2*known_bytes
assert charged==8252864
compact=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
runtime=j(P/exp['inputs']['runtime_mapping']['path']);minimal_contract=compact({'source_files':exp['source_files'],'runtime_mapping':runtime});lower=len(minimal_contract);assert lower==114744
# These three canonical policy-review body copies are already in the recovery
# machine. Coalescing requires a NEW actual sealed review layout and new refs.
provenance=j(V/'CLOSURE01.json')['provenance'];coalesce=[]
for n in ['MACHINE01.json','REPORT01.md','MANIFEST01.json']:
 original=PV/n;copy=next(x for x in provenance if x['original_path']==str(original));assert read(original)==read(Path(copy['path']));coalesce.append({'role':'review_'+{'MACHINE01.json':'machine','REPORT01.md':'report','MANIFEST01.json':'manifest'}[n],'original_reference':str(original),'current_recovery_copy':copy['path'],'sha256':copy['sha256'],'bytes':copy['bytes'],'proposed_relative_path':'policy-review/'+n,'new_actual_path':None,'copies_must_remain_byte_identical':True})
saved=2*sum(x['bytes'] for x in coalesce);assert saved==271114
budget={'limit_bytes':8388608,'target195_two_reads':2*sum(x['bytes'] for x in target),'inputs11_two_reads':2*sum(x['bytes'] for x in inputs),'registration_two_reads':2*len(read(gatepath)),'known_total_first_reads':known_bytes,'known_total_including_finish':charged,'remaining_before_unknowns':8388608-charged,'strict_minimum_contract_two_reads':2*lower,'known_plus_strict_min_contract':charged+2*lower,'minimum_overrun_current_layout':charged+2*lower-8388608,'parent_caller_unknown_bytes':None,'remaining_contract_fields_unknown_bytes':None,'final_review_unknown_bytes':None,'three_parent_proofs_unknown_bytes':None,'all_unknown_body_charge_factor':2,'coalescence_saved_charged_bytes':saved,'coalesced_known_plus_contract_lower_bound':charged-saved+2*lower,'coalesced_remaining_for_other_unknowns_charged':8388608-(charged-saved+2*lower),'coalesced_remaining_unique_bytes':(8388608-(charged-saved+2*lower))//2,'complete_future_fit_proven':False,'no_cap_increase':True,'no_receipt_omission':True}
# Exact AST locations form a bounded source-call inventory, not execution.
locations=[]
for path,b in [(S/'preclaim01.py',source),(R/'parent01.py',parent)]:
 for node in ast.walk(ast.parse(b)):
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)):locations.append({'source':str(path),'sha256':sha(b),'name':node.name,'line':node.lineno,'end_line':node.end_lineno})
unknowns=[{'role':r,'path':None,'sha256':None,'bytes':None,'reason':why} for r,why in [('actual_source_commit','Root adoption and exact committed source/design must complete'),('final_parent_root','New canonical unused external Parent; old Parent is permanently spent'),('parent01.py','Must migrate exact contextual predicates and call accepted preclaim before attempt/spawn'),('final_parent_contract','Actual source/registration/source map/runtime/caller/helpers/three proof refs'),('final_parent_review','Different-author final seven-field release; excludes itself from contract hash'),('cumulative','Actual independently accepted prospective20 evidence bound to new genuine source/gate'),('full_recovery','Actual complete new source/registration/Parent/witness recovery; existing composed proof excludes later supplement'),('independent_source_input_runtime','Actual no-claim genuine admission and current source/runtime/input evidence with exact eight external refs')]]
proofs['final_parent_contract']=None;proofs['final_parent_review']=None
save('EXTERNAL_REFS_CURRENT01.json',{'status':'ACTUAL_EIGHT_REFS_TWO_UNKNOWN_CURRENT_LAYOUT_OVER_BUDGET','refs':proofs,'execution_authority':False})
save('READ_INVENTORY01.json',{'schema_version':1,'inputs':inputs,'target_source':target,'external':external,'recovery_receipts':receipts,'unchanged_helpers':helpers,'registration':{'path':str(gatepath),'future_path':str(CAP/preview['new_gate_path']),'bytes':len(read(gatepath)),'sha256':sha(read(gatepath))},'known_reader_path_count':len(known),'budget':budget,'optional_new_layout':coalesce,'unknowns':unknowns,'source_locations':locations,'reader_semantics':'path-keyed cache, first physical read and finish physical reread; final whole-signature sample; no content-hash cache or budget reset'})
save('SOURCE_READBACK01.json',{'actual_read_files':len(reads),'actual_read_bytes':sum(x['bytes'] for x in reads.values()),'sources':list(reads.values()),'preview_adoption_not_asserted':True,'no_lifecycle_or_numerical_or_network':True,'parent_source_sha256':sha(parent),'old_request_bytes':len(oldrequest)})
print(json.dumps(budget,sort_keys=True))
