"""Create only this source-preparation tree, never a live Parent or CAP."""
from pathlib import Path
import ast, hashlib, json
H=Path(__file__).resolve().parent
OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
PR=H.parent/'financial-wrapper-continuation-proof-reuse01-2026-10-05'
TARGET='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01'
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01'
REF='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
PRED='financial-wrapper-classification-eager-predict-compatibility-20261004-01'
PLANNED='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
REG='fixture_inputs/financial_wrapper_continuation01/gates.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def write(n,b):
 with (H/n).open('xb') as f:f.write(b)
old=(OLD/'parent01.py').read_bytes()
assert sha(old)=='424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0'
write('original_parent01.py',old)
q=json.loads((OLD/'REQUEST_FINAL01.json').read_bytes())
helpers={}
for n in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):
 raw=(OLD/n).read_bytes();assert sha(raw)==q['helper_hashes'][n];write(n,raw);helpers[n]=sha(raw)
raw=(PR/'preclaim_reuse01.py').read_bytes();assert sha(raw)=='079df4afd2ad9cc0c303c400df48aca05f22fceba66fe363f0d0147bfe94800c';write('preclaim01.py',raw);helpers['preclaim01.py']=sha(raw)
raw=(PR/'PROOF_REUSE_CONTRACT_DRAFT01.json').read_bytes();write('proof_reuse_contract01.json',raw);helpers['proof_reuse_contract01.json']=sha(raw)
write('GATE4_DRAFT01.json',(PR/'GATE4_DRAFT01.json').read_bytes())
s=old.decode();edits=[]
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);edits.append({'old':a,'new':b})
replace("PARENT=Path('"+str(OLD)+"')","PARENT=Path('"+TARGET+"')")
replace("IDENTITY='"+REF+"'","IDENTITY='"+ID+"'\n# Only build01.py may replace this exact null binding after actual source joins.\nSOURCE_BINDING=None")
replace("require(q['source']==q['design_source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','fixed actual source/design')", "require(type(SOURCE_BINDING)is dict and q['source']==q['design_source']==SOURCE_BINDING['source'],'Root-adopted actual source/design required')")
replace("require(q['registration']=='fixture_inputs/financial_wrapper_compatibility01/gates.json' and q['registration_sha256']=='e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806' and len(q['source_files'])==354 and len(q['input_hashes'])==11,'fixed actual registration/source/input cardinality')", "require(q['registration']=='"+REG+"' and q['registration_sha256']==SOURCE_BINDING['registration_sha256'] and sha(R.encode(q['source_files']))==SOURCE_BINDING['source_map_sha256'] and len(q['input_hashes'])==29,'exact adopted registration/source and29 input roles')")
replace("q['expected_phase']=='complete100','fixed independent unused compatible100 reference context'", "q['expected_phase']=='continue100','fixed unused continuation context'")
replace("'PROTOCOL_PINS01.json','preclaim01.py'},'exact parent helper closure'", "'PROTOCOL_PINS01.json','preclaim01.py','proof_reuse_contract01.json'},'exact parent helper closure'")
replace("names=sorted(q['source_files']);require(len(names)==354,'fixed354 selected source count')", "names=sorted(q['source_files']);require(len(names)==SOURCE_BINDING['source_count'],'actual closed selected source count')")
replace("len(tracked)==355 and set(tracked)==set(names)|{q['registration']},'complete actual355 source closure'", "len(tracked)==SOURCE_BINDING['tracked_count'] and set(tracked)==set(names)|{q['registration']},'complete actual adopted source closure'")
replace("three spent failures stay counted", "four spent histories stay counted")
replace("len(reg['experiments'])==13,'unchanged program and preserved historical12'", "set(reg['experiments'])=={"+repr(ID)+","+repr(PRED)+","+repr(PLANNED)+",'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'},'four definitions; original13 gate preserved separately'")
replace("require(exp['parent'] is None,'independent complete100 reference has no experiment parent')", "require(exp['parent']=="+repr(PLANNED)+",'direct original plannedFAILED parent; reference is separate')")
replace("require(set(x.name for x in (CAP/'research_runs').iterdir())=={old_id,planned_id,reference_failed_id,'.lock'},'all three original spent histories remain exact')", "reference_complete_id="+repr(REF)+"\n for name,pin in {'claim.json':'c6c1106de459a89f9633ae51501959ecabd47c204534d85e9ebcf15671bcd19f','complete.json':'bd54cb0052645e77fa7b0a4f943ab864798a4e05224ee530d4117b47f8f032c1'}.items():require(sha(R.read(CAP,'research_runs/'+reference_complete_id+'/'+name))==pin,'preserved genuine completed100 reference')\n require(not os.path.lexists(CAP/'research_runs'/reference_complete_id/'failed.json'),'completed reference cannot become failed')\n require(set(x.name for x in (CAP/'research_runs').iterdir())=={old_id,planned_id,reference_failed_id,reference_complete_id,'.lock'},'all four spent histories remain exact')")
replace("len(exp['inputs'])==11,'eleven exact initial and compatibility proof inputs'", "len(exp['inputs'])==29,'29 exact continuation, ancestry and compatibility inputs'")
new=s.encode();ast.parse(s);write('parent01.py',new)
back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back.encode()==old
write('INVERSE01.json',encode({'original_sha256':sha(old),'candidate_sha256':sha(new),'edits':edits,'full_byte_inverse':True,'full_ast_inverse':ast.dump(ast.parse(back))==ast.dump(ast.parse(old))}))
for k in ('source','design_source','registration_sha256','source_files','input_hashes','final_review'):q[k]=None
q.update(status='DRAFT_NOT_RELEASED',parent_root=TARGET,identity=ID,registration=REG,expected_phase='continue100',caller_sha256=sha(new),helper_hashes=helpers)
q['proofs']={k:None for k in q['proofs']}
write('REQUEST_DRAFT01.json',encode(q))
write('SOURCE_MANIFEST_DRAFT01.json',encode({'schema_version':1,'source':None,'registration':REG,'registration_sha256':None,'source_files':None,'tracked_count':None}))
print(json.dumps({'parent_sha256':sha(new),'parent_bytes':len(new),'literal_edits':len(edits),'helper_count':len(helpers),'draft_only':True}))
