import ast,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent;MROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');PREP=B/'paper-treatment-root-composition-adoption-preparation02-2026-10-04';ROOTREC=B/'paper-treatment-root-main-integration01-2026-10-04';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def check(n,v):assert v,n;checks.append(n)
def save(n,v):(O/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
sys.path.insert(0,str(PREP));sp=importlib.util.spec_from_file_location('adoption_reviewed_source',PREP/'recipe02.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
before=json.loads((ROOTREC/'BEFORE01.json').read_bytes());receipt=json.loads((ROOTREC/'INTEGRATION01.json').read_bytes());base=json.loads((PREP/'BASELINE01.json').read_bytes());closure=json.loads((PREP/'CLOSURE01.json').read_bytes());guards=json.loads((PREP/'SCIENTIFIC_GUARDS01.json').read_bytes());check('exact accepted closure',sha((PREP/'CLOSURE01.json').read_bytes())=='833b30f52f9365fd681bfaeea8031909fe938db7bb46e33ab9082f8a8d8961b1');check('original whole composition preserved',sha((PREP/'MANIFEST01.json').read_bytes())=='a81e3f63881deb038d25eb61821874dd89b4ae887936483195ed8be32d5d11b8')
head=R._git_bytes(MROOT,'rev-parse','HEAD').decode().strip();check('actual precommit81022',head==receipt['actual_main_parent_commit']==before['actual_main_before']=='81022cc2f30c4aa2bf58a076eb6cff8d03c30b69');check('before historical135',before['baseline']==base and base['source_count']==135)
R.verify_source(MROOT,closure['sources']);check('actual Main complete138 type/hash/mode/OID',True);check('actual onchain130',len(list((MROOT/'tradingagents/research/onchain_replication').glob('*.py')))==130)
old=set(base['sources']);new=set(closure['sources']);changed={n for n in old if base['sources'][n]!=closure['sources'][n]};added=new-old;check('four changed-threeadded131preserved',len(changed)==4 and len(added)==3 and len(old-changed)==131);check('Root changed denominator exact',set(receipt['changed'])==changed|added)
for n,pin in closure['sources'].items():
 raw=R.bounded(MROOT/n);check('candidate installed '+n,raw==(PREP/'candidate'/n).read_bytes());ast.parse(raw);check('AST '+n,True)
 if n in receipt['changed']:check('Root pin '+n,sha(raw)==receipt['changed'][n])
for n in changed:
 backup=ROOTREC/(Path(n).name+'.original');check('saved original raw '+n,sha(backup.read_bytes())==base['sources'][n]['sha256'])
R._git_tree(MROOT,base['head'],base['sources']);R._git_tree(MROOT,head,base['sources']);check('historical and still-committed135 anchor',True)
static=closure['producer_static_pins'];selfpath=closure['producer_dynamic_self_path'];check('137plus admittedself',len(static)==137 and set(static)==new-{selfpath} and all(sha(R.bounded(MROOT/n))==pin for n,pin in static.items()) and sha(R.bounded(MROOT/selfpath))=='65ffe3efecd0c972341ec2af8deaa2594560b5a36bc9ca2dcd3e1b8da006d81e')
guard_tree={}
for n,pin in guards.items():
 raw=R.bounded(MROOT/n);check('working seven guard '+n,sha(raw)==pin['sha256'] and len(raw)==pin['bytes'] and stat.S_IMODE((MROOT/n).stat().st_mode)==pin['mode']);guard_tree[n]={'git_mode':'100755' if pin['mode']&0o111 else '100644','git_blob_oid':R.blob(raw)}
R._git_tree(MROOT,base['head'],guard_tree);R._git_tree(MROOT,head,guard_tree);check('seven guard committed endpoints',len(guard_tree)==7)
# Genuine old source preparation must now refuse: no135/current138 conflation.
try:R.prepare(str(R.PARENT/'post-integration-review-never-created'/'source'),{k:None for k in R.ROLE_NAMES})
except ValueError as e:check('old135 recipe correctly refuses integrated Main','source closure membership differs' in str(e));save('EXPECTED_OLD_RECIPE_REFUSAL01.json',{'exception':type(e).__name__,'reason':str(e),'target_created':False})
else:raise AssertionError('old recipe unexpectedly accepted actual138')
# Pure registration closure changes must refuse without changing actual Main.
for n in closure['sources']:
 pins=dict(closure['sources']);pins[n]=dict(pins[n],sha256='0'*64)
 try:R.verify_source(MROOT,pins)
 except ValueError:check('every installed source pin mutation '+n,True)
 else:raise AssertionError(n)
# Compare full isolated closed capsule/Parent inventories to prior independent closure.
io=B/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04';sys.path.insert(0,str(io));import recovery04 as A
prior=B/'financial-genuine-wrapper-first-attempt-closure-review01-2026-10-04';cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-root-launch-20261004-01')
for root,name in ((cap,'SOURCE_MANIFEST01.json'),(parent,'PARENT_MANIFEST01.json')):
 actual=A.scan(root);expected=json.loads((prior/name).read_bytes());check('complete isolated unchanged '+name,actual==expected);save('CURRENT_'+name,actual)
request=json.loads((parent/'REQUEST_FINAL03.json').read_bytes());check('isolated source d4e remains',R._git_bytes(cap,'rev-parse','HEAD').decode().strip()==request['source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0')
check('no numeric imports',not any(n in sys.modules for n in ('numpy','pandas','torch','scipy')));check('Main HEAD stable',R._git_bytes(MROOT,'rev-parse','HEAD').decode().strip()==head);save('CHECKS01.json',{'count':len(checks),'checks':checks,'actual_main_parent':head,'historical_baseline':base['head'],'source_count':138,'changed':sorted(changed),'added':sorted(added),'unchanged':131,'isolated_capsule_files':sum(x['kind']=='file' for x in json.loads((O/'CURRENT_SOURCE_MANIFEST01.json').read_bytes())['members']),'isolated_parent_files':sum(x['kind']=='file' for x in json.loads((O/'CURRENT_PARENT_MANIFEST01.json').read_bytes())['members']),'Root_receipt_sha256':sha((ROOTREC/'INTEGRATION01.json').read_bytes()),'authority':None});print(len(checks))
