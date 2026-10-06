"""Join frozen final binding to already performed bounded review; no preflight/run."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
FINAL=HERE.parent.parent/'real-data-pilot-final02-2026-10-06'
def sha(b):return hashlib.sha256(b).hexdigest()
check=json.loads((HERE/'CHECK01.json').read_bytes())
evidence=check['evidence'].copy()
correction=json.loads((HERE/'BINDING_CORRECTION_RECOVERY_CHECK01.json').read_bytes())
evidence.update(correction['evidence'])
def add(p):
    b=p.read_bytes();evidence[str(p.relative_to(ROOT))]=sha(b)
    return json.loads(b) if p.suffix=='.json' else b
binding=add(FINAL/'BINDING01.json');draft=add(FINAL/'BINDING_DRAFT03.json')
review=add(HERE/'BINDING_REVIEW01.json');br=binding['binding_review']
assert br['path']==str((HERE/'BINDING_REVIEW01.json').relative_to(ROOT)) and br['sha256']==evidence[br['path']]
assert draft['binding_review'] is None and draft['status']=='DRAFT_NOT_RELEASED'
draft['binding_review']=br;draft['status']='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE';assert draft==binding
assert evidence[str((FINAL/'BINDING01.json').relative_to(ROOT))]=='bfbb7836c5a315189aa365a7921fa8919ffa349d9f16f6d1b841e8819de24188'
for ref in binding.values():
    if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():assert evidence.get(ref['path'])==ref['sha256'],ref['path']
transport=json.loads((FINAL/'TRANSPORT_BINDING01.json').read_bytes())
assert transport['source_request']['prepared']==binding['preparation']
gate=json.loads((FINAL/'gate01.json').read_bytes());exp=gate['experiments'][binding['identity']]
assert all(evidence[p]==h for p,h in exp['source_files'].items())
assert all(evidence[v['path']]==v['sha256'] for v in exp['inputs'].values())
for name in ('CHECK01.json','BINDING_CORRECTION_RECOVERY_CHECK01.json','DRAFT_BINDING_FINDING01.txt','check01.py','close01.py'):add(HERE/name)
preflight=FINAL/'preflight01.py';assert sha(preflight.read_bytes())==evidence[str(preflight.relative_to(ROOT))]
finding={'severity':'P1','status':'resolved_in_final_binding','file':'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final02-2026-10-06/preflight01.py','line':153,'problem':'Draft02 preparation reference omitted bytes168483, failing strict equality with actual binder source_request.prepared.','impact':'Prospective entry would refuse before native attempt.','resolution':'Draft02 preserved; Draft03/final BINDING01 use exact existing three-field prepared reference. Final whole-reference equality verified.'}
not_tested=['No scientific numerical values, model fits, matching, PnL, timing leakage, returns/cashflows, fees/funding or performance claims tested.',
 'No native job, network, claim, Owner/Binding or full runtime preflight invoked.',
 'Final committed-HEAD authentication, current installed runtime, fresh namespace/process/active-claim checks, physical RAM/disk/complete writable union and native controls remain entry requirements.',
 'No full-pilot capacity/throughput/training completion claim; prior434s failure is not MCM speed.',
 'External recovery proof reused from genuine separate independent review; no body/archive retransmission or POSIX/runtime/unrelated-store claim.']
report={'schema_version':1,'decision':'accepted','identity':binding['identity'],'reviewer':'independent pilot_correction_review','scope':'Combined final changed-seam source/input/binding/recovery composition review. Exact conditional entry release; live committed admission and native eligibility remain mandatory.','findings':[finding],
 'verified':['Exact one-ID inverses for accepted corrected builder9c673 and scalar controls; successor source byteidentical; dependencies change exactly builder/control refs.',
 'Preflight inverse limited to fixed ID/path,72→73 and three required prior evidence references. RootIO changes only fixed ID. No admission/opaque/context/role check removed.',
 'All201actual public source bytes match gate; all178 tradingagents package pins identical to accepted old gate/release. Inputs59 have nine rebound refs and50unchanged; numerical input hashes reused from immutable accepted release without numeric reads.',
 'One actual full metadata prepare equals saved ebe5dcfc. Complete binder inverse and whole generated-document transformation preserve every unrelated field.',
 'Both compact descriptors bindfedb41e0; both archive descriptors join57182e5f, pair/import/stage hashes and both MCM routes join admitted inputs. Producer-only journal/binding output fields remain unchanged.',
 'Same science/32motifs512spent/16decisions28lookback/seven graphs/model/training/runtime/resources. Archive and run namespaces fresh; parentNone, sole identity02, extension73 accepted7fe95.',
 'Final bindingbfbb7836 authenticates six-ref independent673eb40f review; exact prepared reference shape fixed.',
 'Actual failed outcome9941387 joins accepted fresh recovery0ca97db8 and complete2bd5f362. BYTE491520/38regular10directories48names only; actual native/Root0 cleanuptrue; old failed identity and originals retained.',
 'Protected private transport119689 public digest joined and file stat/mode600,parent700,owner/link/path/size checked. No private body opened.',
 'Final release evidence covers every201source59input, preparer8dependencies,binder,whole output documents and bindings; exactly one protected private exception remains.'],
 'not_tested':not_tested,'evidence_reuse':'Existing accepted release and correction review retained; no broad historical matrix/financial rerun.','higher_effort_needed':False}
(HERE/'REVIEW01.json').write_text(json.dumps(report,indent=2)+'\n');add(HERE/'REVIEW01.json')
release={'schema_version':1,'decision':'accepted','identity':binding['identity'],'reviewer':'independent pilot_correction_review','scope':'EXACT_CONDITIONAL_SOURCE_AND_METADATA_ENTRY_RELEASE','evidence':dict(sorted(evidence.items())),
 'binding_sha256':evidence[str((FINAL/'BINDING01.json').relative_to(ROOT))],'binding_review_sha256':br['sha256'],'preflight_sha256':evidence[str(preflight.relative_to(ROOT))],'root_io_sha256':evidence[str((FINAL/'root_io.py').relative_to(ROOT))],
 'cardinality':{'gate_source_pins':201,'gate_input_roles':59,'unchanged_package_pins':178,'outputs':8,'sole_opaque_private_exceptions':1,'released_unique_references':len(evidence)},
 'conditionality':'Final entry must authenticate every public evidence body at committed HEAD, current source/runtime/genuine admission effective73,parentNone, unused fixed02 namespaces, absent competing native/program claims, fresh complete writable union plus unchanged modeled growth,10GiBfloor/9GiBstartup RAM and native controls. Actual Owner/Binding still required. No bypass or successful outcome is granted.',
 'protected_input':'Sole119689 archive_transport body not opened; actual public binder digest and private stat joined. Mandatory existing entry opaque validator authenticates exact bytes.',
 'recovery':'Actual independently accepted failed increment BYTE recovery only; original01 permanentlyFAILED/spent/no refund/relaunch.',
 'resolved_finding':finding,'scientific_or_capacity_claim':False,'runtime_outcomes':None,'not_tested':not_tested}
(HERE/'RELEASE_REVIEW01.json').write_text(json.dumps(release,indent=2,sort_keys=True)+'\n')
files={}
for p in sorted(HERE.iterdir()):
    if p.is_file() and p.name!='MANIFEST01.json':
        b=p.read_bytes();files[p.name]={'bytes':len(b),'sha256':sha(b)}
(HERE/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'status':'ACCEPTED_CONDITIONAL_FINAL_SOURCE_INPUT_ENTRY_COMPOSITION','files':files},indent=2)+'\n')
for name in ('REVIEW01.json','RELEASE_REVIEW01.json','MANIFEST01.json'):print(name,sha((HERE/name).read_bytes()))
print('evidence_refs',len(evidence))
