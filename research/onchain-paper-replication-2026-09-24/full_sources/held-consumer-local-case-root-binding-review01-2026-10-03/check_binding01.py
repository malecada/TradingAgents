import hashlib,json,os,stat,subprocess,sys,runpy
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');P=F/'held-consumer-local-case-metadata-preparation02-2026-10-03';PAY=P/'capsule_payload';R=F/'held-consumer-local-case-root-binding01-2026-10-03';D=F/'held-consumer-local-case-current-design-readback01-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest();doc=lambda p:json.loads(p.read_bytes());HEAD='d443208795f59292c156c5b81b687594efacea4d';PARENT='4e1e021e93ba807690c77309574bae07663695cc';ANCHOR='0cfc2c03200880534b7c91c2f16ac659a265a35b'
env=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
def git(*args,data=None):return subprocess.check_output(['git','-c','protocol.allow=never','-C',str(S),*args],input=data,env=env,stderr=subprocess.PIPE,timeout=30)
def tree(ref):
 out={}
 for row in git('ls-tree','-rz',ref).split(b'\0'):
  if row:
   l,n=row.split(b'\t');mode,kind,oid=l.decode().split();assert kind=='blob';out[n.decode()]=(mode,oid)
 return out
def batch(refs):
 raw=git('cat-file','--batch',data=('\n'.join(refs)+'\n').encode());off=0;out=[]
 for ref in refs:
  end=raw.index(b'\n',off);oid,kind,size=raw[off:end].split();size=int(size);off=end+1;b=raw[off:off+size];off+=size;assert len(b)==size and raw[off:off+1]==b'\n';off+=1;assert hashlib.sha1(kind+b' '+str(size).encode()+b'\0'+b).hexdigest()==oid.decode();out.append(b)
 assert off==len(raw);return out
def body(p):
 a=p.lstat();assert p.resolve()==p and stat.S_ISREG(a.st_mode) and a.st_nlink==1;b=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_dev,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_dev,z.st_size,z.st_mtime_ns,z.st_ctime_ns);return b
for where in [R,D,P]:
 for row in doc(where/'MANIFEST01.json')['files']:
  b=body(where/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
binding=doc(R/'ACTUAL_BINDING01.json');assert binding['actual_source_commit']==binding['actual_design_source']==HEAD
assert git('rev-list','--parents','-n','1','HEAD').decode().split()==[HEAD,PARENT]
old=tree(PARENT);new=tree(HEAD);anchor=tree(ANCHOR);assert len(old)==204 and len(new)==246
payload={p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()};assert len(payload)==42 and set(new)-set(old)==payload and all(new[n]==old[n] for n in old)
committed=dict(zip(new,batch([v[1] for v in new.values()])))
for n,b in committed.items():assert body(S/n)==b
for row in binding['new_metadata_files']:
 n=row['path'];b=body(S/n);assert b==body(Path(row['origin']))==body(PAY/n) and sha(b)==row['sha256'] and len(b)==row['bytes'] and stat.S_IMODE((S/n).stat().st_mode)==row['mode']==stat.S_IMODE((PAY/n).stat().st_mode)
prior=doc(F/'held-consumer-root-source-composition07-2026-10-03/SOURCE_COMPOSITION07.json');entries=prior['source_entries'];assert len(entries)==199
for row in entries:
 n=row['target'];assert sha(body(S/n))==row['sha256'] and new[n]==old[n]
 if row['package_source']:assert new[n]==anchor[n]
for row in prior['copied_opaque_and_closed_history_files']:
 p=S/row['path'];assert body(p)==body(Path(row['original_path'])) and sha(body(p))==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode']
expected=set(new)|{r['path'] for r in prior['copied_opaque_and_closed_history_files']};actual=set()
for root,dirs,files in os.walk(S,followlinks=False):
 if Path(root)==S:dirs.remove('.git')
 for n in dirs:
  q=Path(root)/n;assert not q.is_symlink() and any(k.startswith(q.relative_to(S).as_posix()+'/') for k in expected)
 for n in files:
  q=Path(root)/n;body(q);actual.add(q.relative_to(S).as_posix())
assert actual==expected and len(actual)==288
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert set(git('ls-files','--others','--exclude-standard').decode().splitlines())==expected-set(new)
gate=doc(S/'held-fixture-registration01.json');ceilings=[]
for d in (S/'research_runs').iterdir():
 c=doc(d/'claim.json');t=doc(d/'failed.json');assert gate['experiments'][d.name]==c['experiment'] and t['claim_sha256']==sha(body(d/'claim.json')) and t['status']=='failed' and not (d/'complete.json').exists();ceilings.append(c['effective_attempt_budget'])
 for n,h in t['output_sha256'].items():assert sha(body(d/'outputs'/n))==h
assert sorted(ceilings)==[2,3,4,5]
sys.path.insert(0,str(S));module=runpy.run_path(str(S/'proof_tools/build_release_draft01.py'));rows=[{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in entries];results={}
for case in ['success','failure']:
 refs=doc(P/(case+'-roles01.json'));result=module['held_metadata_draft'](S,HEAD,ANCHOR,rows,refs,design_source=HEAD);assert result==doc(D/(case+'-current-design-readback01.json'))
 assert result['status']=='draft-not-released' and result['execution_admitted'] is False and result['registration_authority'] is None and result['budget_authority'] is None and result['native_release'] is None
 aux=result['input_plan']['auxiliary_metadata'];assert aux['committed_metadata_readback'] is True and aux['current_source']==aux['design_source']==HEAD and aux['admission_source_count']==204
 plan=result['input_plan'];assert len(plan['input_rows'])==33 and len(plan['observed_metadata'])==15
 for row in plan['input_rows'].values():assert sha(body(S/row['path']))==row['sha256']
 evidence=doc(S/refs['original_evidence']['path']);assert body(S/evidence['control_reference']['path'])==body(S/plan['input_rows']['original_import']['path'])
 runtime=result['runtime_readback'];assert runtime['record_count']==251 and runtime['record_bytes']==5033917
 results[case]={'inputs':33,'roles':15,'pins':204,'current_design_equal':True,'runtime_records':251,'status':result['status']}
assert not any(n.split('.')[0] in ('numpy','torch','scipy') for n in sys.modules)
assert git('rev-parse','HEAD').decode().strip()==HEAD and len(list((S/'research_runs').iterdir()))==4
out={'head':HEAD,'parent':PARENT,'anchor':ANCHOR,'new_payload_files':42,'tracked_files':246,'nonGit_files':288,'source_files':199,'package_files':148,'prior_extra_files_unchanged':42,'old_claim_ceilings':sorted(ceilings),'new_claims':0,'cases':results,'native_release':False,'external_recovery':False,'numerical_imports':False}
(H/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS genuine d443 solechild4e1e/42exactaddedmodes/199148unchanged/246tracked288nonGit/42oldextras+4FAILED; BOTH actualinstalleddraft currentdesign204/33/15/251 matchRoot;noadmission/native')
