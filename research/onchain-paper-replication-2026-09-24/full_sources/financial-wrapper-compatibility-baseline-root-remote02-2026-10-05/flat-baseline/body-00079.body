from pathlib import Path
import types,json,hashlib
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-wrapper-compatibility-coalesced-evidence-correction04-2026-10-04';O=F/'financial-wrapper-compatibility-coalesced-evidence-root03-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');M=types.ModuleType('exact_source04');M.__file__=str(P/'copy_layout01.py');exec(compile((P/'copy_layout01.py').read_bytes(),M.__file__,'exec'),M.__dict__);PC=M.PC;assert hashlib.sha256(M.PRECLAIM_BYTES).hexdigest()=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16';gate=json.loads((CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json').read_bytes());exp=gate['experiments']['financial-wrapper-classification-eager-complete100-compatibility-20261004-01'];r=PC.Reader();inputs=PC.Inputs(CAP,exp['inputs'],r);policy=inputs.json('operational_source_compatibility');refs={}
for kind,name in [('proof','ORIGINAL_RECOVERY_PROOF01.json'),('machine','MACHINE01.json'),('report','REPORT01.md'),('manifest','MANIFEST01.json')]:
 p=O/name;body=p.read_bytes() if kind=='proof' else (D/'candidates'/name).read_bytes();refs['recovery_'+kind]={'path':str(p),'sha256':hashlib.sha256(body).hexdigest()}
try:PC._proof_bundle('recovery',refs,inputs,policy,r)
except FileNotFoundError as e:
 assert str(O/'MACHINE01.json') in str(e);result={'status':'GENUINE_PRECLAIM_PROOF_BUNDLE_REFUSES_UNINSTALLED_CANDIDATE','missing_path':str(O/'MACHINE01.json'),'real_registered11_inputs':True,'literal_actual_c5_proof_join_reached':True,'actual_root_modified':False,'refs':refs,'full_preclaim_executed':False,'authority_granted':False}
else:raise AssertionError('uninstalled recovery machine accepted')
r.finish();(D/'PENDING_INSTALL01.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
