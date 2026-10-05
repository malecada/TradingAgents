import ast,hashlib,json,os
from pathlib import Path
root=Path.cwd();c=root/'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04'
old=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01');new=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
identity='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01';oldid='financial-wrapper-classification-eager-continue100-compatibility-20261004-01'
def encode(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 with p.open('xb') as w:w.write(b)
def sha(b):return hashlib.sha256(b).hexdigest()
assert not os.path.lexists(new);new.mkdir(mode=0o700)
q=json.loads((old/'REQUEST_FINAL01.json').read_bytes());roles=set(q['input_hashes'])|{'continuation_source_successor','continuation_source_successor_review','continuation_source_successor_recovery','successor_original_closure','successor_refusal'};assert len(roles)==34
raw=(old/'parent01.py').read_bytes();text=raw.decode();assert sha(raw)=='5c0bab39643c61ffd36483ad466c203aa5df77a3a1749217a085d284d9051b66'
def once(a,b):
 global text
 assert text.count(a)==1,a[:100];text=text.replace(a,b)
once("PARENT=Path('"+str(old)+"')","PARENT=Path('"+str(new)+"')")
once("IDENTITY='"+oldid+"'","IDENTITY='"+identity+"'")
line=next(x for x in text.splitlines() if x.startswith('SOURCE_BINDING='));once(line,'SOURCE_BINDING=None')
once("q['registration']=='fixture_inputs/financial_wrapper_continuation01/gates.json'","q['registration']=='fixture_inputs/financial_wrapper_continuation_successor01/gates.json'")
once("len(q['input_hashes'])==29","set(q['input_hashes'])=="+repr(set(sorted(roles))))
once("set(exp['inputs'])==set(q['input_hashes']) and len(exp['inputs'])==29","set(exp['inputs'])==set(q['input_hashes'])=="+repr(set(sorted(roles))))
once("'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'},'four definitions; original13 gate preserved separately'","'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','"+identity+"'},'original four definitions plus one same-family successor; original13 gate preserved separately'")
once("=='5f478bc3570aab21ffdfa32e1215aeddbf085e5d33a3da3a8131cfb0c4aff655','accepted exact compatible claimed-run and runtime correction required'","==SUCCESSOR_FIXTURE_SHA256,'accepted exact successor compatibility fixture required'")
once('PREFIX=\'tradingagents/research/onchain_replication/\'','PREFIX=\'tradingagents/research/onchain_replication/\'\nSUCCESSOR_FIXTURE_SHA256=None')
text=text.replace('and29 input roles','and34 exact input roles').replace('29 exact continuation, ancestry and compatibility inputs','34 exact continuation, ancestry and compatibility inputs')
ast.parse(text);put(new/'parent01.py',text.encode())
helpers={}
for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):
 b=(old/name).read_bytes();assert sha(b)==q['helper_hashes'][name];put(new/name,b);helpers[name]=sha(b)
contract=json.loads((old/'proof_reuse_contract01.json').read_bytes());contract['consumer']=identity;contract['current_source']=None;put(new/'proof_reuse_contract01.json',encode(contract))
for key in ('source','design_source','registration_sha256','source_files','input_hashes','caller_sha256','helper_hashes','final_review'):q[key]=None
q.update(status='DRAFT_NOT_RELEASED',parent_root=str(new),identity=identity,registration='fixture_inputs/financial_wrapper_continuation_successor01/gates.json',proofs={'cumulative':None,'full_recovery':None,'independent_source_input_runtime':None})
put(new/'REQUEST_DRAFT01.json',encode(q))
record={'schema_version':1,'status':'draft-not-released','parent':str(new),'identity':identity,'old_parent':str(old),'old_caller_sha256':sha(raw),'draft_caller_sha256':sha(text.encode()),'unchanged_helpers':helpers,'input_roles':sorted(roles),'source_binding':None,'fixture_binding':None,'preclaim':'pending exact candidate','qualification':'reversible preparation only; no Admission, ResearchRun.start, claim, intent, numerical import or launch'}
put(c/'SUCCESSOR_PARENT_DRAFT_PREPARATION01.json',encode(record));print(json.dumps({'parent':str(new),'unchanged_helpers':len(helpers),'input_roles':len(roles),'draft':True}))
