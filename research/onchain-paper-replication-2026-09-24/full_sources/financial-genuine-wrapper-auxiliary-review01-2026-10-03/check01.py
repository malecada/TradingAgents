import ast,copy,hashlib,json,os,re,stat,sys,time
from email.parser import BytesParser
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-auxiliary-preparation01-2026-10-03';G=P/'generated02';C=F/'financial-genuine-wrapper-root-charter-draft01-2026-10-03';sys.path.insert(0,str(P));import build_aux01 as B
checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,m):
 assert v,m
 checks.append(m)
def refuse(f,m):
 try:f()
 except ValueError:checks.append('refused '+m)
 else:raise AssertionError(m)
def read(p,limit=4*1024**2,links=False):
 p=Path(p);s=p.lstat();ck(stat.S_ISREG(s.st_mode) and (s.st_nlink>=1 if links else s.st_nlink==1) and s.st_size<=limit and p.resolve()==p,'regular canonical bounds');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);chunks=[];total=0
 try:
  ck(B.R.sig(os.fstat(fd))==B.R.sig(s),'open stable')
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=limit,'bounded read');chunks.append(b)
  ck(total==s.st_size and B.R.sig(s)==B.R.sig(os.fstat(fd))==B.R.sig(p.lstat()),'unchanged body');return b''.join(chunks)
 finally:os.close(fd)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pinned '+Path(p).name);return json.loads(b)
ck(sha(read(P/'build_aux01.py'))=='7c5d58a07b7ac49ba8c167ce3e7722dcd69cb030c501b47c482b8cc6067ff436','final builderpin');m=doc(P/'MANIFEST01.json','3dd7bf4055087876d6ed925e0c30a9f43b7516906a840037d1d12c46dcdfaa8e');actual=set()
for r in m['members']:
 p=P/r['path'];s=p.lstat();actual.add(r['path']);ck(stat.S_IMODE(s.st_mode)==r['mode'],'typed manifestmode')
 if r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'typed directory')
 elif r['kind']=='symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'typed symlink target no dereference')
 else:
  ck(stat.S_ISREG(s.st_mode) and s.st_nlink==r['links'],'honest hardlinks');b=read(p,links=True);ck(len(b)==r['bytes'] and sha(b)==r['sha256'],'manifest opaque hash')
ck({str(p.relative_to(P)) for p in P.rglob('*')}==actual|{'MANIFEST01.json'} and len(actual)==123,'exact typed123 candidate scope');refs,values=B.origins();source=B.authenticate_sources(values);ck(source==doc(G/'SOURCE_READBACK01.json')['rows'] and len(source)==194,'genuine sourceGit194 current matches draft');ck(not (B.CAP/'uv.lock').exists(),'actual missing financialroot lock remainshold')
draft=doc(G/'DRAFT01.json','34438a5011ca7dac6ddf1890aa9d4d57b76d1560d7dc32a351343ba62897a7a1');mapping=doc(G/'runtime_mapping.json');runtime=doc(G/'RUNTIME_READBACK01.json');env=doc(G/'environment.DRAFT.json');prior=doc(B.PRIOR_RUNTIME,B.PRIOR_RUNTIME_SHA256)
ck(B.baseline_runtime_join(mapping)['all251_prior_records_equal'],'actual all251 baseline pins');ck(mapping['python']=='3.13.13' and mapping['executable']==sys.executable and mapping['prefix']==sys.prefix,'actual runtimeversion/path');exe=Path(sys.executable).resolve();s=exe.lstat();ck(s.st_size==31510904 and stat.S_ISREG(s.st_mode) and s.st_nlink==1,'actual interpreter extent');h=hashlib.sha256();fd=os.open(exe,os.O_RDONLY|os.O_NOFOLLOW);total=0
try:
 while True:
  b=os.read(fd,65536)
  if not b:break
  h.update(b);total+=len(b);ck(total<=64*1024**2,'streamed interpreter bound')
 ck(B.R.sig(s)==B.R.sig(os.fstat(fd))==B.R.sig(exe.lstat()),'interpreter unchanged')
finally:os.close(fd)
ck(h.hexdigest()==mapping['executable_sha256']==runtime['interpreter']['sha256']=='1b6373b55566df2953fe1e1345aec5df0d2e76c5e385871e68aa46c48020803d','actual interpreter fullhash');site=Path(sys.prefix)/'lib/python3.13/site-packages';dirs={p for p in site.iterdir() if p.name.endswith('.dist-info')};ck(len(dirs)==251 and all(not p.is_symlink() and p.is_dir() for p in dirs),'complete251actualdistdirs');seen=set();runtimebytes=0;hardlinked=0;meta={r['name']:r for r in runtime['metadata']}
for row in mapping['distribution_records']:
 rp=Path(row['record']);ck(rp.parent in dirs and rp.name=='RECORD','actual distributionrecord path');record=read(rp,links=True);md=read(rp.parent/'METADATA',links=True);message=BytesParser().parsebytes(md,headersonly=True);name=re.sub(r'[-_.]+','-',message['Name']).lower();ck(name==row['name'] and name not in seen and message['Version']==row['version'] and sha(record)==row['record_sha256'],'actual METADATA version and RECORD hash');seen.add(name);ck(meta[name]['metadata_sha256']==sha(md) and meta[name]['metadata_bytes']==len(md) and meta[name]['record_bytes']==len(record),'independent metadata pins');runtimebytes+=len(md)+len(record);hardlinked+=int(rp.stat().st_nlink>1)+int((rp.parent/'METADATA').stat().st_nlink>1)
ck(len(seen)==251 and runtimebytes==runtime['metadata_bytes']==7765398,'complete actual runtime metadata bytecount');ck(all(env[k] is None for k in ['torch_version','cuda_available','cuda_build']) and runtime['torch_imported'] is False and runtime['dependency_bodies_fully_rehashed'] is False,'no fabricated liveTorch/dependencybodyclaims');ck(sha(read(B.MAIN/'uv.lock'))==mapping['lock_sha256']==B.LOCK,'actualMainlockpin')
for name in ['uv.lock','pyproject.toml','.python-version']:ck(read(G/('proposed-'+name))==read(B.MAIN/name),'proposed separate auxiliary '+name)
for n,key in [('model.json','model.json'),('training.json','training.json'),('synthetic_recipe.json','RECIPE01.json'),('source_closure.json','SOURCE_CLOSURE01.json')]:ck(read(G/n)==values[key],'exact accepted copied body '+n)
ck(set(p.name for p in G.iterdir())==set(draft['auxiliary_pins'])|{'DRAFT01.json'},'exact47auxdrafts plusdraft')
for n,ref in draft['auxiliary_pins'].items():
 b=read(G/n);ck(ref['prepared_path']==str(G/n) and ref['bytes']==len(b) and ref['sha256']==sha(b),'actualauxiliary pin '+n)
plans=json.loads(values['PHASE_TEMPLATES01.json'])['templates'];dag=json.loads(values['PHASE_DAG01.json']);job0=json.loads(values['JOB_TEMPLATE01.json']);job0['resources']['disk_paths']=[str(B.CAP)];job0['resources']['storage_budget']['root']=str(B.CAP)
for i,slot in enumerate(draft['slots']):
 ck(slot['slot_index']==i+1 and slot['logical_key_not_identity']==dag['rows'][i]['logical_key_not_identity'] and slot['dependencies']==dag['rows'][i]['dependencies'],'phase order/dependency');ck(set(slot['inputs'])==B.BASE_INPUTS,'exact8 inputs')
 for role,ref in slot['inputs'].items():ck(ref['path'] is None and ref['dataset'] is None and sha(read(Path(ref['prepared_path'])))==ref['sha256'],'all144 realdraft joins')
 plan=doc(Path(slot['inputs']['wrapper_plan']['prepared_path']));job=doc(Path(slot['inputs']['execution_job']['prepared_path']));ck(plan==plans[i] and all(plan[n] is None for n in ['experiment','namespace','cell_id']),'unreserved original plan');ck(job==job0,'job only disk/storage root changes');ck(slot['admitted'] is False and slot['actual_outcome'] is None,'no phase result')
ck(len(draft['slots'])==18 and all(v is None for v in draft['future'].values()) and draft['future_admitted_source_total'] is None and draft['paper_financial_fit_credit']==0,'allactualauthority withheld');refuse(lambda:B.refuse_runnable(draft),'unconditional release refusal')
# Independent tiny read-only metadata/source distinctions; own hardlinks and symlink only.
tiny=O/'opaque';tiny.write_bytes(b'metadata');os.link(tiny,O/'opaque-hardlink');(O/'opaque-link').symlink_to(tiny);refuse(lambda:B.stream_pin(tiny),'singlelink source/interpreter');ck(B.stream_pin(tiny,32,runtime_metadata=True)==b'metadata','read-only metadatahardlink');refuse(lambda:B.stream_pin(tiny,3,runtime_metadata=True),'metadata extent');refuse(lambda:B.stream_pin(O/'opaque-link',32,runtime_metadata=True),'symlink metadata');refuse(lambda:B.parse_tree(b'100644 blob '+b'z'*40+b'\tx.py\0'),'badGitOID');refuse(lambda:B.parse_tree(b'100644 blob '+b'a'*40+b'\tx.py'),'unterminatedGit')
for key in ['prefix','resolved_executable','lock_sha256']:
 x=copy.deepcopy(mapping);x[key]='wrong';refuse(lambda:B.baseline_runtime_join(x),'changed originalruntime '+key)
x=copy.deepcopy(mapping);x['distribution_records'].append(copy.deepcopy(x['distribution_records'][0]));refuse(lambda:B.baseline_runtime_join(x),'duplicatenormalizeddistribution');x=copy.deepcopy(mapping);x['distribution_records'][0]['record_sha256']='0'*64;refuse(lambda:B.baseline_runtime_join(x),'changed originalrecord')
# Charter review is a draft consistency check, not cumulative admission.
charter=doc(C/'CHARTER_DRAFT01.json','060e13c4534747393591e30f60ba38fe105a9b8782260a0b75575cf3b7775564');ck(charter['status']=='DRAFT_NOT_RELEASED' and charter['cumulative_budget']['actual_allowance'] is None and charter['cumulative_budget']['independent_review'] is None and all(v is None for v in charter['release_requirements'].values()),'charter admission genuinely absent');cp=charter['phases'];ck(len(cp)==18 and len({r['proposed_identity'] for r in cp})==18 and len({r['proposed_cell'] for r in cp})==10,'18proposedidentities10cells');by={r['logical_key_not_identity']:r for r in cp}
for row,original in zip(cp,dag['rows'],strict=True):
 ck(all(row[k]==v for k,v in original.items()),'charter preserves exactDAG row');ck(row['actual_identity_reserved'] is False and row['original_schedule_epochs']==100,'noreservation/original100epochs');ck(row['proposed_dependencies']==[by[k]['proposed_identity'] for k in row['dependencies']],'actual proposeddependency mapping')
 if row['phase'] in ['continue100','predict']:ck(row['proposed_cell']==by[row['dependencies'][0]]['proposed_cell'],'continued/predict samecell')
 if row['phase']=='continue100':ck(row['proposed_cell']!=by[row['dependencies'][1]]['proposed_cell'],'reference distinctcell')
ck(charter['denominator']==dag['expected_dispositions_if_all_contracts_met'],'exactdenominator');ck(sum(r['optimizer_updates_if_successful'] for r in cp)==804 and sum(r['training_fit_cell_calls'] for r in cp)==12,'conditional804updates12fitcalls');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'decision':'ACCEPTED_AUXILIARY_SOURCE_AND_DRAFT_ONLY_NOT_REGISTRATION_OR_BUDGET','checks':len(checks),'candidate_manifest_members':123,'source_members':len(source),'interpreter_bytes':total,'runtime_distributions':len(seen),'runtime_metadata_bytes':runtimebytes,'hardlinked_runtime_metadata_files':hardlinked,'draft_slots':18,'draft_input_joins':144,'charter_cells':10,'source_commit':B.COMMIT,'live_torch_fields':None,'financial_root_lock_present':False,'actual_allowance':None,'native_or_scientific_authority':False};(O/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
