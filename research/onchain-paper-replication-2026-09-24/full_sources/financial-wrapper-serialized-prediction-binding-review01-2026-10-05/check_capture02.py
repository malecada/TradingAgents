from pathlib import Path
import hashlib,json,tarfile,stat,collections
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';D=Path(__file__).parent;OUT=F/'financial-wrapper-serialized-prediction-current-capture01-2026-10-05';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');REMOTE=F/'financial-wrapper-serialized-prediction-source-remote01-2026-10-05'
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
cap=load(OUT/'CAPTURE01.json');root=C/'SERIALIZED_PREDICTION_CURRENT_CAPTURE_ROOT_EXIT01.json';assert sha(root.read_bytes())=='fe382cb0f6f34643eb18887f46e6723b8cb39798bc688734d1755218a9e65cca' and load(root)['actual_exit']==0
assert (C/'SERIALIZED_PREDICTION_CURRENT_CAPTURE02.stderr').read_bytes()==b'' and load(C/'SERIALIZED_PREDICTION_CURRENT_CAPTURE02.stdout')==cap
assert cap['source']=='4c66c404fd61ccdbb62c39cd91e16878df74a232' and cap['CAP_regular']==1188 and cap['CAP_typed']==1530 and cap['new_original_bodies']==109 and cap['new_original_bytes']==1580043
archive=OUT/'increment.tar.gz';assert archive.stat().st_size==683272 and sha(archive.read_bytes())==cap['archive']['sha256']=='e22abea2dd16f158e9536e1f90609894e04a2037cd31a69971875fa41043c106'
manifest=load(OUT/'archive-manifest.json');assert sha((OUT/'archive-manifest.json').read_bytes())==cap['archive']['manifest_sha256']=='7fb7a4132e3749ba2bccfd934fb65c8597280dd60ce002dd3219105fc661c910';rows={r['path']:r for r in manifest['members']};assert len(rows)==110 and all(r['kind']=='file' for r in rows.values())
composition=load(OUT/'snapshot/COMPOSITION01.json');assert composition['source']==cap['source'] and composition['basis']==cap['basis'];prior=load(F/'financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/new-bodies/COMPOSITION01.json')
mapped=composition['materialized'];assert len(mapped)==109 and len({r['flat'] for r in mapped.values()})==109 and set(rows)=={r['flat'] for r in mapped.values()}|{'COMPOSITION01.json'}
origins={'CAP':CAP,'Git':CAP/'.git','Parent':P,'review-phase':D,'Root':C,'source-recovery':REMOTE};counts=collections.Counter();opaque_hashes={}
for name,refrow in mapped.items():
 label,rel=name.split('/',1);counts[label]+=1;p=OUT/'snapshot'/refrow['flat'];body=p.read_bytes();s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sha(body)==refrow['sha256'] and len(body)==refrow['bytes'];r=rows[refrow['flat']];assert r['sha256']==refrow['sha256'] and r['bytes']==refrow['bytes'] and r['mode']==stat.S_IMODE(s.st_mode)
 original=origins[label]/rel;assert sha(original.read_bytes())==refrow['sha256'];opaque_hashes[refrow['flat']]=refrow['sha256']
assert counts=={'CAP':11,'Git':44,'Parent':11,'review-phase':24,'Root':14,'source-recovery':5}
assert sum(r['bytes'] for r in mapped.values())==1580043
body=(OUT/'snapshot/COMPOSITION01.json').read_bytes();assert sha(body)==rows['COMPOSITION01.json']['sha256'] and len(body)==rows['COMPOSITION01.json']['bytes'];opaque_hashes['COMPOSITION01.json']=sha(body)
# Standard-library archive inspection only; no extraction, imports or tensor decode.
seen=set()
with tarfile.open(archive,'r:gz') as tf:
 for t in tf:
  assert t.name in rows and t.name not in seen and t.isfile() and not t.issym() and not t.islnk();r=rows[t.name];assert t.size==r['bytes'] and t.mode==r['mode'];b=tf.extractfile(t).read();assert sha(b)==opaque_hashes[t.name];seen.add(t.name)
assert seen==set(rows)
newcap={r['path']:r for r in composition['capsule']['members']};oldcap={r['path']:r for r in prior['capsule']['members']};changed={n for n in oldcap if newcap[n]!=oldcap[n]};assert changed=={'fixture_inputs/financial_wrapper_serialized_storage01/gates.json',*['tradingagents/research/onchain_replication/'+n for n in ['evaluation.py','financial_wrapper_fixture.py','operational_source_compatibility.py']]};assert len(set(newcap)-set(oldcap))==8 and len(newcap)==1530 and sum(r['kind']=='file' for r in newcap.values())==1188
assert {name[4:] for name in mapped if name.startswith('CAP/')}==changed|{n for n in set(newcap)-set(oldcap) if newcap[n]['kind']=='file'}
oldgit={r['path']:r for r in prior['Git']['manifest']['members']};newgit={r['path']:r for r in composition['Git']['manifest']['members']};reused=[]
for n,r in newgit.items():
 if r['kind']!='file':continue
 if 'Git/'+n in mapped:assert mapped['Git/'+n]['sha256']==r['sha256'] and mapped['Git/'+n]['bytes']==r['bytes']
 else:
  parts=Path(n).parts;assert len(parts)==3 and parts[0]=='objects' and len(parts[1])==2 and len(parts[2])==38 and all(c in '0123456789abcdef' for c in ''.join(parts[1:]));assert oldgit[n]==r;reused.append(n)
assert len(reused)==454 and sum(r['kind']=='file' for r in newgit.values())==498 and len(composition['Git_object_inventory'])==473
for label in ['Parent','review-phase']:
 manifest2=composition[label]['manifest'];files={r['path']:r for r in manifest2['members'] if r['kind']=='file'};assert set(files)=={n.split('/',1)[1] for n in mapped if n.startswith(label+'/')}
 for n,r in files.items():assert mapped[label+'/'+n]['sha256']==r['sha256'] and mapped[label+'/'+n]['bytes']==r['bytes']
q=load(P/'REQUEST_PRESERVATION_DRAFT01.json');assert q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and q['proofs']['full_recovery'] is None
for role,name in [('cumulative','CUMULATIVE_PROOF01.json'),('independent_source_input_runtime','SOURCE_INPUT_RUNTIME_PROOF01.json')]:assert q['proofs'][role]==ref(D/name)
for n in ['Root/SERIALIZED_PREDICTION_CURRENT_CAPTURE01.py','Root/SERIALIZED_PREDICTION_CURRENT_CAPTURE01_WITHHELD.json','Root/SERIALIZED_PREDICTION_CURRENT_CAPTURE02.py','review-phase/CURRENT_CAPTURE_FINDING01.json','review-phase/CURRENT_CAPTURE_ENTRY_RELEASE02.json']:assert n in mapped
assert composition['immutable_writer_exclusion'] is composition['POSIX_reconstruction'] is composition['installed_runtime_body_recovery'] is composition['numerical_authority'] is False
check={'schema_version':1,'decision':'accepted-actual-current-increment-capture-not-external-recovery','source':cap['source'],'identity':cap['identity'],'capture':ref(OUT/'CAPTURE01.json'),'actual_root_exit':ref(root),'source_capture02':ref(C/'SERIALIZED_PREDICTION_CURRENT_CAPTURE02.py'),'archive':dict(path=str(archive),**cap['archive']),'archive_manifest':ref(OUT/'archive-manifest.json'),'composition':ref(OUT/'snapshot/COMPOSITION01.json'),'scope_counts':dict(counts),'materialized_originals':109,'materialized_bytes':1580043,'archive_bodies':110,'CAP_regular':1188,'CAP_typed':1530,'CAP_reused_regular':1177,'Git_regular':498,'Git_logical_objects':473,'Git_reused_loose_regular':454,'Parent_regular':11,'review_phase_regular':24,'original_and_archive_bytes_joined':True,'all_actual_typed_scope_and_inheritance_joins':True,'basis':composition['basis'],'withheld_source01_retained':True,'external_recovery':False,'final_envelope_recovery':False,'numerical_authority':False,'qualification':'Actual new increment archive and all109 original-byte mappings authenticated once. Unchanged CAP/Git bodies inherited through accepted6bbe/9fc; no old body rescan. Original native nulls/unknowns and fixed scientific criteria retained. External receiver and fresh archive restoration remain required.'}
with (D/'CURRENT_CAPTURE_CHECK01.json').open('x') as f:f.write(json.dumps(check,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(ref(D/'CURRENT_CAPTURE_CHECK01.json')))
