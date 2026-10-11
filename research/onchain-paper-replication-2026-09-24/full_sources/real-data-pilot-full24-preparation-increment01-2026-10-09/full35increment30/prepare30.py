"""Generate prospective public35 helper sources only; never execute them."""
import ast,difflib,hashlib,json,os,re,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;O=H.parent/'nativeoutcome29';F=H.parent.parent
owned=['real-data-pilot-full35-'+n+'01-2026-10-11' for n in ('binding-preparation','entry-preparation','cumulative-preparation')]+['pilot35-'+n+'01-2026-10-11' for n in ('binding-source-candidate','binding-source-review','entry-source-candidate','entry-source-review','generated-public-review','actual-binding-review','cumulative-machine-review','binding-release-review','preparation-increment-tools-review')]+['pilot34-two-attribute-main-adoption01-2026-10-11','pilot34-two-attribute-main-integration-bundle01-2026-10-11','pilot34-native03-increment-return-review01-2026-10-11']
helpers=('select30.py','capture30.py','recover30.py','prepare30.py','check_source30.py','HELPERS_MANIFEST01.json','AUTHOR_CHECK01.json','PROSPECTIVE_ROSTER01.json','PREPARATION_CHECK01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff','REPORT.md')
oldroster=json.loads((O/'PROSPECTIVE_ROSTER01.json').read_bytes())
priorfiles=[n.replace('28.json','29.json').replace('commit28.','commit29.') for n in oldroster['prior_generated_files']]+['STAGING_UNAVAILABLE01.json']
plan=json.loads((F/'pilot34-two-attribute-main-integration-bundle01-2026-10-11/INSTALLATION_PLAN01.json').read_bytes())
mainpins={m['destination']:m['result_sha256'] for m in plan['modules']}
fixed=oldroster['fixed_public_names']+['research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/ADMISSION01.json', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/admission-stdout01.txt', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/admission-stderr01.txt', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/BINDING01.json', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/RELEASE_REVIEW01.json']
recovery_hash='d297b714a4cc2cc014a026040d85cd2da537e50b3eab94e273edd08abbc54609'
review_hash='a522ca34f5e90c317002d3431875aab2896afeb64b01c9bc710d5454aacaa9e7'
def once(text,mapping):
 for token in mapping:assert token in text,token
 return re.sub('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)),lambda m:mapping[m.group()],text)
def assignment(text,name,value):
 start=text.index(name+'=') if name+'=' in text else text.index(name+' =');end=text.index('\n',start)
 return text[:start]+name+'='+repr(value)+text[end:]
select_map={'postnative28/FRESH_GIT_RECOVERY28.json':'nativeoutcome29/FRESH_GIT_RECOVERY29.json','c66a488a8bad2b51710769464c41ff92b3f0377e3f5d6ebc52733fb486fbf660':recovery_hash,'pilot34-postnative-increment-return-review01-2026-10-11':'pilot34-native03-increment-return-review01-2026-10-11','71e99df6ce8daf7226c2b91a42716cbbd35fd97d1bd6a9656365918f6d35259b':review_hash,"prior.parent/'CAPTURE28.json'":"prior.parent/'CAPTURE29.json'","prior.parent/'SELECTION28.json'":"prior.parent/'SELECTION29.json'",'post-native-increment28.tar':'native-outcome-increment29.tar','fresh-git-recovered-postnative28.tar':'fresh-git-recovered-nativeoutcome29.tar',"HERE/'SELECTION29.json'":"HERE/'SELECTION30.json'",'actual28':'actual29','accepted28':'accepted29','generated28':'generated29','selection29 already spent':'selection30 already spent','generated nativeoutcome29':'generated full35increment30','declared nativeoutcome29 scope':'declared full35increment30 scope'}
select=once((O/'select29.py').read_text(),select_map)
for name,value in [('owned',owned),('prior_generated_names',priorfiles),('helper_names',helpers),('main_source_names',list(mainpins)),('fixed_public_names',fixed)]:select=assignment(select,name,value)
select=select.replace('# Main installation is outside this preparation; only public bundle bodies.', 'main_source_pins='+repr(mainpins)+'\nfor relative,expected in main_source_pins.items():\n    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink() and sha(ROOT/relative)==expected, relative\n    names.add(relative)')
start=select.index("    'selection_rule': ");end=select.index('\n',start)
select=select[:start]+"    'selection_rule': 'Finite fresh35 public preparation and reviews, exact installed ten Main sources and actual29 postcapture receipts. Prior rows reused only on exact typed body match; inherited coverage retained through authenticated actual29 receipt. No empirical/private/runtime stores or deletion authority.',"+select[end:]
capture_map={'SELECTION29.json':'SELECTION30.json','CAPTURE29.json':'CAPTURE30.json','native-outcome-increment29.tar':'full35-preparation-increment30.tar','Complete declared public nativeoutcome29 increment':'Complete declared public full35increment30 increment'}
recover_map={'Recover the one declared nativeoutcome29 public increment':'Recover the one declared full35increment30 public increment','real-pilot-native03-outcome-20261011-29.git':'real-pilot-full35-preparation-20261011-30.git','FRESH_GIT_RECOVERY29.json':'FRESH_GIT_RECOVERY30.json','GIT_OPERATIONS29.json':'GIT_OPERATIONS30.json','CAPTURE29.json':'CAPTURE30.json','fresh-git-recovered-nativeoutcome29.tar':'fresh-git-recovered-full35increment30.tar','Complete declared nativeoutcome29 public increment only':'Complete declared full35increment30 public increment only'}
texts={'select':select,'capture':once((O/'capture29.py').read_text(),capture_map),'recover':once((O/'recover29.py').read_text(),recover_map)}
patch=[];inverse=[]
for name,text in texts.items():
 ast.parse(text)
 with (H/(name+'30.py')).open('x') as f:f.write(text)
 before=(O/(name+'29.py')).read_text();patch.extend(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile=name+'29.py',tofile=name+'30.py'));inverse.extend(difflib.unified_diff(text.splitlines(True),before.splitlines(True),fromfile=name+'30.py',tofile=name+'29.py'))
for name,text in [('LITERAL_PATCH01.diff',''.join(patch)),('LITERAL_INVERSE01.diff',''.join(inverse))]:
 with (H/name).open('x') as f:f.write(text)
roster={'status':'PROSPECTIVE_UNEXECUTED','owned_public_roots':owned,'main_source_names':list(mainpins),'main_source_pins':mainpins,'helper_names':helpers,'prior_generated_files':priorfiles,'fixed_public_names':fixed,'select_literal_map':select_map,'capture_literal_map':capture_map,'recovery_literal_map':recover_map,'baseline_source':'f8222a31bab1bc40caebddf9a160eb20fc174e96','baseline_recovery_sha256':recovery_hash,'accepted_return_sha256':review_hash,'scopes':[],'helpers_executed':False}
with (H/'PROSPECTIVE_ROSTER01.json').open('x') as f:json.dump(roster,f,indent=2,sort_keys=True);f.write('\n')
print('SOURCE_GENERATION_ONLY; selection/capture/recovery not executed')
