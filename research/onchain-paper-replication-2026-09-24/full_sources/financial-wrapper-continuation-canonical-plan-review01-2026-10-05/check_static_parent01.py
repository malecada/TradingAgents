"""Review literal ten-body Parent candidate, never invoke optional builder."""
from pathlib import Path
import ast,copy,json,os,sys
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-wrapper-continuation-canonical-parent-preparation01-2026-10-05'
OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01');NEW=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01');CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');SOURCE='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();manifest=json.loads(rd.read(A/'MANIFEST01.json','56687f3765ca1f74b384b6c0e8dcf10861695410438fe8fb29a4ce1f1fc87911'))
for row in manifest['members']:
 if row['kind']=='file':raw=rd.read(A/row['path'],row['sha256']);rd.need(len(raw)==row['bytes'],'full frozen preparation body extent')
rd.need([r for r in R.scan(A)['members'] if r['path']!='MANIFEST01.json']==manifest['members'],'complete author typed frozen namespace')
oldraw=rd.read(OLD/'parent01.py','b50d1e727979a989f3da1e18a5b204cc3d29169ad425806e8550aa88af5ed0be');newraw=rd.read(A/'candidate/parent01.py','5c0bab39643c61ffd36483ad466c203aa5df77a3a1749217a085d284d9051b66');oldq=json.loads(rd.read(OLD/'REQUEST_DRAFT01.json'));newqraw=rd.read(A/'candidate/REQUEST_DRAFT01.json','678667541715d562dc03a09ef12c84a51c8ef08c70c393fca1322352401da7ef');newq=json.loads(newqraw)
m=json.loads(rd.read(F/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_SOURCE_MANIFEST01.json','1cc3b8796a656db8df02ecec0c871cdd575f4164ef58decda2326ce3fb42be46'));gate=json.loads(rd.read(CAP/m['registration'],m['registration_sha256']));e=gate['experiments'][newq['identity']]
binding={'source':SOURCE,'registration_sha256':m['registration_sha256'],'source_map_sha256':R.digest(R.encode(m['source_files'])),'source_count':359,'tracked_count':360}
oldline=next(line for line in oldraw.decode().splitlines(keepends=True) if line.startswith('SOURCE_BINDING='));newline='SOURCE_BINDING='+repr(binding)+'\n';oldpath="PARENT=Path('"+str(OLD)+"')";newpath="PARENT=Path('"+str(NEW)+"')"
rd.need(newraw==oldraw.decode().replace(oldline,newline).replace(oldpath,newpath).encode(),'exact only two literal caller header changes')
reverse=newraw.decode().replace(newline,oldline).replace(newpath,oldpath);rd.need(reverse.encode()==oldraw and ast.dump(ast.parse(reverse))==ast.dump(ast.parse(oldraw)),'complete byte and AST inverse')
oldcontract=rd.read(OLD/'proof_reuse_contract01.json','d46aa04a41b530d0e497ca8c423beacab58d778a7241839084ac0751a38da033');newcontract=rd.read(A/'candidate/proof_reuse_contract01.json','706ed7b0b927af36d03b493cb1c437f0d82f469fa82d250f7f6da08380124315')
rd.need(oldcontract.count(b'664e2ca5fa11d6640ab79f64c5aa222aeb3a9128')==1 and newcontract==oldcontract.replace(b'664e2ca5fa11d6640ab79f64c5aa222aeb3a9128',SOURCE.encode()),'only honest current source in reuse contract changes')
expected=copy.deepcopy(oldq);expected.update(source=SOURCE,design_source=SOURCE,parent_root=str(NEW),registration_sha256=m['registration_sha256'],source_files=m['source_files'],input_hashes={k:v['sha256'] for k,v in e['inputs'].items()},caller_sha256=R.digest(newraw),proofs={k:None for k in oldq['proofs']},final_review=None,status='DRAFT_NOT_RELEASED');expected['helper_hashes']['proof_reuse_contract01.json']=R.digest(newcontract)
rd.need(expected==newq and R.encode(expected)==newqraw,'entire exact source/input/null-authority draft rebind')
files={}
for name,h in newq['helper_hashes'].items():
 raw=rd.read(A/'candidate'/name,h);files[name]={'sha256':h,'bytes':len(raw)}
 if name!='proof_reuse_contract01.json':rd.need(raw==rd.read(OLD/name,oldq['helper_hashes'][name]),'seven actual unchanged helper bodies')
files.update({'parent01.py':{'sha256':R.digest(newraw),'bytes':len(newraw)},'REQUEST_DRAFT01.json':{'sha256':R.digest(newqraw),'bytes':len(newqraw)}})
rd.need(len(files)==10 and {r['path'] for r in R.scan(A/'candidate')['members']}==set(files),'exact ten static candidate body denominator')
rd.need(len(newq['input_hashes'])==29 and len(newq['source_files'])==359 and newq['expected_phase']=='continue100' and all(v is None for v in newq['proofs'].values()) and newq['final_review'] is None,'no fabricated proof or release')
head=rd.read(CAP/'.git/HEAD').decode().strip();actual=rd.read(CAP/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;rd.need(actual==SOURCE and not os.path.lexists(NEW) and not os.path.lexists(CAP/'research_runs'/newq['identity']),'actual current source and fresh unused target/identity')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_EXACT_STATIC_CANONICAL_PARENT_CANDIDATE_ONLY','source':SOURCE,'target':str(NEW),'caller_sha256':R.digest(newraw),'request_sha256':R.digest(newqraw),'reuse_contract_sha256':R.digest(newcontract),'allowed_files':files,'builder_execution_allowed':False,'withheld_builder_sha256':'4d08136c891107ee9a0f776632bd06ec51a94e850433d5299e5a2203012898fc','checks':rd.checks,'read_bytes':rd.total,'full_public_preflight_passed':False,'numerical_authority':False};R.put(H/'STATIC_PARENT_READBACK01.json',result)
release=dict(result,decision='ACCEPTED_EXACT_TEN_BODY_PARENT_LITERAL_INSTALLATION_ONLY',candidate_root=str(A/'candidate'),root_must_authenticate_installed_outputs_and_final_source=True,readback={'path':str(H/'STATIC_PARENT_READBACK01.json'),'sha256':R.digest(R.encode(result))})
R.put(H/'STATIC_PARENT_INSTALL_RELEASE01.json',release);print(json.dumps({'release_sha256':R.digest(R.encode(release)),'readback_sha256':R.digest(R.encode(result)),'checks':rd.checks}))
