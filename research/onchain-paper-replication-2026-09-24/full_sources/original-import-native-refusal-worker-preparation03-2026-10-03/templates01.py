"""Deterministic prospective release/registration generation; no writes or admission."""
import copy,hashlib,json
from refusal_inventory03 import POLICY
from refusal_cases import NAMES,PRECLAIM,NO_OWNER,NO_JOURNAL,identity,policy
from mutation_inputs import render,draft_gate
PROGRAM='original-import-refusal-engineering-20261003'
def prepare(base,primary_gate,*,source_files,runtime_hashes,imported_identity_source,runtime,native_environment,capsule,source_commit):
    if base['source_anchor']!=source_commit:raise ValueError('base source anchor differs from prospective capsule')
    package={k:v for k,v in source_files.items() if k.startswith('tradingagents/')}
    if len(package)!=144:raise ValueError('exact composed144 package required')
    rendered={name:render(base,name,package) for name in NAMES}
    gate,charters=draft_gate(primary_gate,rendered,source_files,runtime_hashes,imported_identity_source=imported_identity_source)
    if gate['program_id']!=PROGRAM:raise ValueError('separate refusal program required')
    cases={}
    for name,item in rendered.items():
        exp=gate['experiments'][identity(name)];job=json.loads(item['files'][item['inputs']['execution_job']['path']])
        cases[name]={'identity':identity(name),'experiment':exp,'job_resources':job['resources'],'expectation':policy(name),'execution_route':'guarded-real-job-admission-before-claim' if name in PRECLAIM else 'real-job-launch-monitor-worker-ResearchRun','oracle_pairs':0 if name in NO_OWNER else 64}
    release={'status':'draft-not-released','remaining':['exact composed source/Git and runtime review','committed separate engineering charter/gate','independent worker/outer/oracle review','root one-use release and native capacity check'],
      'inventory_policy':copy.deepcopy(POLICY),'program_id':PROGRAM,'family':gate['families']['import-refusal-engineering'],'capsule_root':capsule,'capsule_commit':source_commit,'source_files':copy.deepcopy(source_files),'runtime':copy.deepcopy(runtime),'native_environment':copy.deepcopy(native_environment),'registration':'fixture_inputs/refusal-registration.json','registration_sha256':hashlib.sha256((json.dumps(gate,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)).encode()).hexdigest(),'cases':cases}
    protocol={'variants':27,'classes':16,'preclaim':list(PRECLAIM),'max_claims':23,'max_owners':17,'max_journals':19,'max_oracle_pairs':17*64,'max_scored_pairs':129,'automatic_retries':0,'paper_budget_authority':False,'financial_fits':0,'actual_attempts':0,'sequential_cases_only':True,'case_order':list(NAMES),'same_capsule_family_ledger_required':True,'per_case_native_seconds':1800,'per_case_outer_active_seconds':1840,'per_case_closure_seconds':None,'entire_suite_wall_bound_seconds':None,'whole_outer_deadline_enforced':False,'inventory_policy':copy.deepcopy(POLICY),'limits_qualification':'1GiB sampled whole-tree stop;10GiB disk floor;3GiB worker high=max/swap0;4MiB file;8KiB all new inventory pages/indexes and authority metadata. Native1800/active-loop1840 have checks; no whole-outer or51300-second suite wall bound is claimed. Later readiness/remaining storage may defer unused cases without retrying closed ones.'}
    assert sum(x['oracle_pairs'] for x in cases.values())==1088 and sum(n not in NO_OWNER for n in NAMES)==17 and sum(n not in NO_JOURNAL for n in NAMES)==19
    return {'rendered':rendered,'charters':charters,'registration':gate,'release':release,'protocol':protocol}
