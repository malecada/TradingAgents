from pathlib import Path
import json,hashlib,ast,shutil
base=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources')
a=base/'financial-wrapper-compatibility-final-bundle-transport-preparation01-2026-10-04'; d=base/'financial-wrapper-compatibility-final-bundle-transport-preparation02-2026-10-05';d.mkdir()
def put(n,v): (d/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ['watch01.py','cohort01.py','receipt01.py','recover.template01.py','restore_bundle01.py','KNOWN_REQUIRED01.json']:shutil.copyfile(a/n,d/n)
shutil.copytree(a/'utilities',d/'utilities')
s=(a/'binding01.py').read_text(); original=s
s=s.replace("FIELDS=('complete_final_request','complete_final_release','complete_three_proofs','coalesced_actual_review','source_runtime_bridge','accepted_baseline_byte_review','independent_final_population_review')",'''COMMON=('accepted_basis_byte_review','coalesced_actual_review','source_runtime_bridge','postinstall_review','independent_population_review')
FINAL=('baseline_envelope','baseline_recovery_review','complete_final_request','complete_final_release','complete_three_proofs')
ROUNDS={'BASELINE':'baseline02','FINAL_SUPPLEMENT':'final-supplement02'}
def evidence(q):
 R.require(type(q)is dict and q.get('round') in ROUNDS,'two fixed rounds only')
 if q['round']=='BASELINE':R.require(all(q.get(k)is None for k in FINAL),'baseline excludes genuinely future proofs and final caller')
 fields=COMMON+(FINAL if q['round']=='FINAL_SUPPLEMENT' else ())
 needed=[]
 for field in fields:
  v=q.get(field)
  if field=='complete_three_proofs':R.require(type(v)is list and len(v)==3 and len({ref(x)['path'] for x in v})==3,'three distinct actual proofs');needed.extend(v)
  else:needed.append(ref(v))
 return fields,needed

def envelope(q,fields):
 r=ref(q.get('envelope'));e=json.loads(body(r))
 R.require(e=={'schema_version':1,'round':q['round'],'source':SOURCE,'bundles':q['bundles'],'evidence':{k:q[k] for k in fields}},'exact nonrecursive envelope')
 R.require(q['exact_required'].get(r['path'])=={k:r[k] for k in ('bytes','sha256')},'envelope selected')
 if q['round']=='BASELINE':R.require(r['path']==PREFIX+'financial-wrapper-compatibility-preclaim-baseline-envelope01-2026-10-05/ENVELOPE01.json','fixed baseline envelope')
 return e''')
s=s.replace("q['status']=='ROOT_FROZEN_FINAL_POPULATION_REQUIRES_CALLER_REVIEW'","q['status']=='ROOT_FROZEN_TWO_ROUND_POPULATION_REQUIRES_CALLER_REVIEW'")
beg=s.index(' needed=[]\n for field in FIELDS:');end=s.index(' for r in needed:',beg)
s=s[:beg]+" fields,needed=evidence(q);envelope(q,fields)\n"+s[end:]
s=s.replace("known=json.loads(R.read(HERE,'KNOWN_REQUIRED01.json'));R.require(all(required.get(k)==v for k,v in known.items()),'all current and failed capture bodies retained')","known=json.loads(R.read(HERE,'KNOWN_REQUIRED01.json'));R.require(q['round']=='FINAL_SUPPLEMENT' or all(required.get(k)==v for k,v in known.items()),'baseline retains all current and failed capture bodies')")
s=s.replace("R.require(any(b['archive']['sha256']", "R.require(q['round']=='FINAL_SUPPLEMENT' or any(b['archive']['sha256']")
s=s.replace("ast.parse(s);return s.encode(),changes","suffix=ROUNDS[q['round']];a='compatibility-final-bundle01';b='compatibility-'+suffix;R.require(s.count(a)==2,'two exact receiver namespace literals');s=s.replace(a,b);changes.append((a,b));ast.parse(s);return s.encode(),changes")
(d/'binding01.py').write_text(s)
put('SOURCE_INVERSE01.json',{'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'original_body':original,'new_sha256':hashlib.sha256(s.encode()).hexdigest(),'changes':'finite round evidence, nonrecursive selected envelope, distinct receiver namespace; original bounded loops unchanged'})
# Emit exact per-round helpers; caller must install only one round closure in a fresh Root namespace.
for kind,suffix in [('BASELINE','baseline02'),('FINAL_SUPPLEMENT','final-supplement02')]:
 p=d/kind;p.mkdir()
 for n in ['watch01.py','cohort01.py','KNOWN_REQUIRED01.json','binding01.py','recover.template01.py']:shutil.copyfile(d/n,p/n)
 shutil.copytree(d/'utilities',p/'utilities')
 # Keep binder ROOT tied to Main, not install-relative nested source directory.
 text=(p/'binding01.py').read_text().replace('ROOT=HERE.parents[3]',"ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')")
 (p/'binding01.py').write_text(text)
 for n in ['receipt01.py','restore_bundle01.py']:
  text=(a/n).read_text().replace('compatibility-final-bundle01','compatibility-'+suffix)
  if n=='restore_bundle01.py':
   text=text.replace('required=B.validate(q)',"required=B.validate(q);R.require(q['round']=="+repr(kind)+",'exact installed round')")
   text=text.replace("'ACCEPTED_EXACT_FINAL_BUNDLE_FLAT'",repr('ACCEPTED_EXACT_'+kind+'_BUNDLE_FLAT'))
   text=text.replace("'FINAL_BUNDLE_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW'",repr(kind+'_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW'))
  (p/n).write_text(text)
 q=json.loads((a/'REQUEST_DRAFT01.json').read_text())
 for k in ['accepted_baseline_byte_review','independent_final_population_review']:q.pop(k)
 q.update(round=kind,envelope=None,status='DRAFT_NOT_RELEASED')
 for k in ['accepted_basis_byte_review','postinstall_review','independent_population_review','baseline_envelope','baseline_recovery_review']:q[k]=None
 put(kind+'/REQUEST_DRAFT01.json',q)
for p in d.rglob('*.py'):ast.parse(p.read_text())
put('PROTOCOL01.json',{'rounds':['BASELINE','FINAL_SUPPLEMENT'],'baseline_excludes':['full_recovery_proof','final_request','final_release'],'baseline_proves':'byte basis plus exact new captured bodies only','final_requires':'actual baseline recovery plus all final caller proofs/request/release and independent review','envelope':'selected external metadata; must not be inserted into archive it hashes','numerical_authority':False,'unchanged_caps':{'file':4194304,'logical':67108864,'allocated':100663296,'members':32768,'floor':10737418240}})
print(d)
