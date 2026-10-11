import hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];Q=F/'pilot34-native-owner-qualification02-2026-10-11'
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
out={'schema_version':1,'decision':'ACCEPTED_REPAIRED_SOURCE_AND_CONDITIONAL_ENGINEERING_ENTRY','reviewer':'independent outcome16_release_review','fixture03_review':ref(P/'FIXTURE03_REVIEW01.json'),'preserved_owner01_refusal':ref(P/'OWNER01_REFUSAL01.json'),'owner02_manifest':ref(Q/'MANIFEST02.json'),'owner02_script':ref(Q/'qualify02.py'),'owner02_command':ref(Q/'COMMAND02.json'),'owner02_result':ref(P/'OWNER02_RESULT01.json'),'scope':'Changed failure latch/reporting and exact command joins only; unchanged source/numerical evidence reused. No native/science/harness execution.','blocking_source_findings':[],'conditional_root_entry':{'maximum_attempts':1,'outer_timeout_seconds':60,'must_precede_execution':['actual pilot34 terminal cleanup and independent outcome acceptance','full failed34 external recovery and independent return acceptance','fresh exact source/runtime/storage/process and one-launch eligibility'],'raw_exit_and_output_retention_required':True,'fresh_conditions_observed_by_reviewer':False},'limitations':['Virtual address-space cap is source-declared, not observed kernel/cgroup proof','Native library body not independently read; hash/extent metadata only','No actual native loader/ABI/seals/numeric equality or performance','No actual Session/checkpoint/upper-chain qualification','No genuine Owner/Binding/admission/financial authority','Two-attribute C helper remains separately unintegrated'],'main_or_registration_mutated':False}
write('REVIEW01.json',out);write('MANIFEST01.json',{'decision':out['decision'],'files':{str(p.relative_to(P)):{k:v for k,v in ref(p).items() if k!='path'} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(P/'REVIEW01.json'),'manifest':ref(P/'MANIFEST01.json')},sort_keys=True))
