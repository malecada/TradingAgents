"""Actual two-file committed delta only; old source body verification is reused."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
H=Path(__file__).resolve().parent;F=H.parent;C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01')
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();before='664e2ca5fa11d6640ab79f64c5aa222aeb3a9128';after='d4c81c0961342bfe4c5771aabbef1d46a14cffb8';commands=[]
def git(*args):
 rd.tick();p=subprocess.run(['git','--no-optional-locks','-C',str(C),*args],capture_output=True,timeout=10,check=False);rd.tick();rd.need(p.returncode==0 and len(p.stdout)<=4*1024*1024 and not p.stderr,'bounded read-only Git metadata command');commands.append({'arguments':list(args),'stdout_sha256':R.digest(p.stdout),'bytes':len(p.stdout)});return p.stdout
rd.need(git('log','-1','--format=%H %P').decode().strip()==after+' '+before,'exact current direct parent commit')
changed=git('diff','--name-only',before,after).decode().splitlines();wanted=['fixture_inputs/financial_wrapper_continuation01/gates.json','fixture_inputs/financial_wrapper_continuation01/prior.json'];rd.need(changed==wanted,'exact only two committed changes')
tracked=git('ls-files','-z').decode().rstrip('\0').split('\0');rd.need(len(tracked)==len(set(tracked))==360,'actual full tracked path denominator')
release=json.loads(rd.read(H/'SOURCE_CORRECTION_RELEASE01.json','4cb08140322df469ce8911fd51c877683f671aee513d7391d09a6523680d77be'))
for item in release['files']:
 raw=rd.read(C/item['path'],item['sha256']);rd.need(raw==git('show',after+':'+item['path']),'actual committed body equals installed accepted candidate');rd.need(R.digest(git('show',before+':'+item['path']))==item['before_sha256'],'original committed body preserved')
rawmanifest=rd.read(F/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_SOURCE_MANIFEST01.json');manifest=json.loads(rawmanifest);gate=json.loads(rd.read(C/wanted[0]));identity='financial-wrapper-classification-eager-continue100-compatibility-20261004-01';definition=gate['experiments'][identity];oldq=json.loads(rd.read(P/'REQUEST_FINAL01.json','c00ce9b4a9410d6045baf957030431f2ef3851ac84fb43436d0e2e013c9cfe63'))
expected=dict(oldq['source_files']);expected[wanted[1]]='b8b4b4f124aebdd5816c8dc0427814139feedd66682f1092bc76c6d25d50b9a9'
rd.need(manifest['source']==after and manifest['source_files']==definition['source_files']==expected and len(expected)==359,'exact old source map plus one changed prior pin')
rd.need(set(tracked)==set(expected)|{wanted[0]} and manifest['registration_sha256']==R.digest(rd.read(C/wanted[0])),'complete tracked/source map relationship and new gate hash')
rd.need(len(definition['inputs'])==29 and len(gate['experiments']['financial-wrapper-classification-eager-predict-compatibility-20261004-01']['inputs'])==17,'both unchanged role denominators')
rd.need(not os.path.lexists(C/'research_runs'/identity),'fixed consumer remains unclaimed')
rd.finish();value={'schema_version':1,'decision':'ACCEPTED_ACTUAL_EXACT_TWO_FILE_COMMITTED_METADATA_DELTA','source':after,'parent_source':before,'changed_paths':changed,'source_manifest':{'path':str(F/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_SOURCE_MANIFEST01.json'),'sha256':R.digest(rawmanifest)},'source_pins':359,'tracked':360,'continue_inputs':29,'predict_inputs':17,'original_committed_bodies_preserved':True,'old818_body_scan_repeated':False,'runtime251_scan_repeated':False,'numerical_authority':False,'commands':commands,'checks':rd.checks,'read_bytes':rd.total};R.put(H/'ADOPTION_READBACK01.json',value);print(json.dumps(value))
