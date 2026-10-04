
# Prepare exact unused Parent context after the genuinely committed source exists.
from pathlib import Path
import ast,hashlib,json,os,stat,subprocess,datetime
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01')
NEW=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
NEWREG='fixture_inputs/financial_wrapper_compatibility01/gates.json'
IDENTITY='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
PRE=FS/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04/preclaim01.py'
def h(b):return hashlib.sha256(b).hexdigest()
def read(p,pin=None):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304 and p.resolve(strict=True)==p
 b=p.read_bytes();assert pin is None or h(b)==pin;return b

def main():
 assert not os.path.lexists(NEW)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP).decode().strip();assert head!='7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
 assert subprocess.run(['git','merge-base','--is-ancestor','7b056a574e3e7b3c7ba209a39ee6a615e649d60c',head],cwd=CAP).returncode==0
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=CAP)
 regraw=read(CAP/NEWREG,'e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806');reg=json.loads(regraw);exp=reg['experiments'][IDENTITY]
 names=subprocess.check_output(['git','ls-files','-z'],cwd=CAP).decode().rstrip('\0').split('\0');assert len(names)==355 and set(names)==set(exp['source_files'])|{NEWREG}
 assert len(exp['source_files'])==354 and len(exp['inputs'])==11 and exp['parent'] is None and len(reg['experiments'])==13
 for n,pin in exp['source_files'].items():assert h(read(CAP/n))==pin
 raw=read(OLD/'parent01.py','7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3');text=raw.decode();pairs=[]
 def replace(a,b):
  nonlocal text
  assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b,1);pairs.append({'old':a,'new':b})
 replace('from descendants01 import pin as process_pin','from descendants01 import pin as process_pin\nimport preclaim01 as PRECLAIM')
 replace("PARENT=Path('"+str(OLD)+"')","PARENT=Path('"+str(NEW)+"')")
 replace("IDENTITY='financial-wrapper-classification-eager-complete100-20261003-01'","IDENTITY='"+IDENTITY+"'")
 replace("q['source']==q['design_source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207'","q['source']==q['design_source']=='"+head+"'")
 replace("q['registration']=='fixture_inputs/financial_wrapper_claimedrun01/gates.json' and q['registration_sha256']=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c' and len(q['source_files'])==338 and len(q['input_hashes'])==8","q['registration']=='"+NEWREG+"' and q['registration_sha256']=='"+h(regraw)+"' and len(q['source_files'])==354 and len(q['input_hashes'])==11")
 replace("'fixed original unused complete100 reference context'","'fixed independent unused compatible100 reference context'")
 replace('def preflight(q):','def preflight(q,contract_ref):')
 replace("'bounded_git01.py','PROTOCOL_PINS01.json'","'bounded_git01.py','PROTOCOL_PINS01.json','preclaim01.py'")
 replace("require(len(names)==338,'fixed338 selected source count')","require(len(names)==354,'fixed354 selected source count')")
 replace("require(len(tracked)==339 and set(tracked)==set(names)|{q['registration']},'complete actual339 source closure')","require(len(tracked)==355 and set(tracked)==set(names)|{q['registration']},'complete actual355 source closure')")
 oldext="exp['cumulative_budget_extension']=={'extension':{'path':'fixture_inputs/financial_wrapper_claimedrun01/extension19.json','sha256':'dfed4dd70d7ed37f3b57f155e1f3acadde6ac673d5261be4a1510a96b0c615e4'},'review':{'path':'fixture_inputs/financial_wrapper_claimedrun01/extension-review19.json','sha256':'3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e'}}"
 newext="exp['cumulative_budget_extension']=="+repr(exp['cumulative_budget_extension']);replace(oldext,newext)
 replace("'base18/prior0 and exact genuine cumulative19 review'","'base18/prior0 and exact genuine cumulative20 review; three spent failures stay counted'")
 replace("len(reg['experiments'])==12,'unchanged program and preserved historical11'","len(reg['experiments'])==13,'unchanged program and preserved historical12'")
 marker="require(not os.path.lexists(CAP/'research_runs'/planned_id/'complete.json'),'planned failed history cannot become complete')"
 add="""\n reference_failed_id='financial-wrapper-classification-eager-complete100-20261003-01'
 for name,pin in {'claim.json':'2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','failed.json':'abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6'}.items():require(sha(R.read(CAP,'research_runs/'+reference_failed_id+'/'+name))==pin,'preserved genuine failed100 history')
 require(not os.path.lexists(CAP/'research_runs'/reference_failed_id/'complete.json'),'failed100 cannot become complete')
 require(set(x.name for x in (CAP/'research_runs').iterdir())=={old_id,planned_id,reference_failed_id,'.lock'},'all three original spent histories remain exact')"""
 replace(marker,marker+add)
 replace("len(exp['inputs'])==8,'eight exact initial inputs'","len(exp['inputs'])==11,'eleven exact initial and compatibility proof inputs'")
 replace("=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','accepted exact claimed-run and runtime correction required'","=='5f478bc3570aab21ffdfa32e1215aeddbf085e5d33a3da3a8131cfb0c4aff655','accepted exact compatible claimed-run and runtime correction required'")
 replace("require(admitted.effective_attempt_budget==19,'actual independently extended numerical ceiling19')","require(admitted.effective_attempt_budget==20,'actual independently extended numerical ceiling20 without refund')")
 replace("return parent,args,command,job,storage,r","metadata=json.loads(reference(q['proofs']['independent_source_input_runtime']));external=metadata['compatibility_preclaim_external_refs']\n require(type(external)is dict and set(external)=={'review_proof','review_machine','review_manifest','review_report','recovery_proof','recovery_machine','recovery_manifest','recovery_report'},'exact eight genuine source/policy evidence refs')\n require(contract_ref=={'path':str(parent/'REQUEST_FINAL01.json'),'sha256':sha(R.read(parent,'REQUEST_FINAL01.json'))},'actual final request reference')\n refs={**external,'final_parent_contract':contract_ref,'final_parent_review':q['final_review']}\n preclaim=PRECLAIM.validate_preclaim(admitted,j,p,refs)\n return parent,args,command,job,storage,r,preclaim")
 replace('def launch(q):\n parent,args,command,job,storage,policy=preflight(q)','def launch(q,contract_ref):\n parent,args,command,job,storage,policy,preclaim=preflight(q,contract_ref)')
 replace("'phase':q['expected_phase']})","'phase':q['expected_phase'],'preclaim_metadata':preclaim})")
 replace("p.add_argument('--launch',action='store_true');a=p.parse_args()","p.add_argument('--launch',action='store_true');p.add_argument('--preflight',action='store_true');a=p.parse_args()")
 replace("if a.launch:raise SystemExit(launch(q))\n else:validate_release(q)","require(not(a.launch and a.preflight),'one explicit mode')\n contract_ref={'path':str(a.request.resolve()),'sha256':a.sha256}\n if a.launch:raise SystemExit(launch(q,contract_ref))\n elif a.preflight:\n  value=preflight(q,contract_ref);print(json.dumps(value[-1],sort_keys=True))\n else:validate_release(q)")
 candidate=text.encode();ast.parse(candidate)
 inverse=text
 for pair in reversed(pairs):
  assert inverse.count(pair['new'])==1;inverse=inverse.replace(pair['new'],pair['old'],1)
 assert inverse.encode()==raw and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(raw),include_attributes=False)
 olddraft=json.loads(read(OLD/'REQUEST_DRAFT01.json'));helpers={n:read(OLD/n,pin) for n,pin in olddraft['helper_hashes'].items()};helpers['preclaim01.py']=read(PRE,'557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16')
 q={**olddraft,'status':'DRAFT_NOT_RELEASED','parent_root':str(NEW),'identity':IDENTITY,'source':head,'design_source':head,'registration':NEWREG,'registration_sha256':h(regraw),'source_files':exp['source_files'],'input_hashes':{r:v['sha256'] for r,v in exp['inputs'].items()},'caller_sha256':h(candidate),'helper_hashes':{n:h(b) for n,b in helpers.items()},'proofs':{'cumulative':{'path':str(CAP/exp['cumulative_budget_extension']['review']['path']),'sha256':exp['cumulative_budget_extension']['review']['sha256']},'full_recovery':None,'independent_source_input_runtime':None},'final_review':None}
 # Compact actual JSON preserves every field; canonical contract hashing is unchanged.
 files={**helpers,'parent01.py':candidate,'REQUEST_DRAFT01.json':(json.dumps(q,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode(),'SOURCE_INVERSE01.json':(json.dumps({'schema_version':1,'original_sha256':h(raw),'candidate_sha256':h(candidate),'full_byte_AST_inverse':True,'literal_changes':pairs},indent=2,sort_keys=True)+'\n').encode()}
 NEW.mkdir(mode=0o700)
 for name,b in files.items():
  fd=os.open(NEW/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  try:os.write(fd,b)
  finally:os.close(fd)
 print(json.dumps({'status':'DRAFT_NOT_RELEASED','source':head,'caller_sha256':h(candidate),'request_sha256':h(files['REQUEST_DRAFT01.json']),'request_bytes':len(files['REQUEST_DRAFT01.json']),'caller_bytes':len(candidate),'helpers':len(helpers),'literal_changes':len(pairs),'new_parent':str(NEW)}))
if __name__=='__main__':main()
