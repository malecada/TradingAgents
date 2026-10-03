"""Read-only real source/Git and opaque-input integration verification."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,tarfile
D=Path(__file__).resolve().parent;F=D.parent;R=F.parents[2]
S=F/'held-consumer-root-source-composition03-2026-10-03';I=F/'held-target-input-reuse-root-collection01-2026-10-03'
h=lambda b:hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
for p,name in [(S,'MANIFEST03.json'),(I,'MANIFEST01.json')]:
 for x in doc(p/name)['files']:
  b=(p/x['path']).read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256']
sb=(S/'SOURCE_COMPOSITION03.json').read_bytes();ib=(I/'INPUT_COLLECTION03.json').read_bytes()
assert h(sb)=='8bcca3db6eb5127117ca9ae5a5b3408adfde54568d1a8fcd4a674427083c2d65'
assert h(ib)=='35c534071525c3656d8ea5969a2d590d490a8edd5916177c648f08c544a70d81'
v=json.loads(sb);q=json.loads(ib);C=Path(v['source_root']);old=C.parent.parent/'held-score-consumer-native-20261003-02'/'source'
# Actual source roots are siblings two levels above /source.
old=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-02/source')
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],env=env,stderr=subprocess.PIPE,timeout=15)
HEAD='903488c49ad25e8026ec849a1c8b30ca5f90bcff';P='76a4bd766722e0f5177412f6945117d9c2b5fc45';A='b8c6c280fb229ffaa5195c95baf3f57485e972b0';O='fb9fad1d93836b4f92f2be8111da4adf22b7e069'
assert git(C,'rev-parse','HEAD').decode().strip()==v['actual_source_commit']==HEAD
assert git(old,'rev-parse','HEAD').decode().strip()==P
assert git(C,'rev-list','--parents','-n','1',HEAD).decode().split()==[HEAD,P]
assert git(C,'rev-list','--parents','-n','1',P).decode().split()==[P,A]
assert git(C,'rev-list','--parents','-n','1',A).decode().split()==[A,O]
assert not (C/'.git/objects/info/alternates').exists()
def tree(root,rev):
 result={}
 for raw in git(root,'ls-tree','-rz',rev).split(b'\0'):
  if not raw:continue
  fields,path=raw.split(b'\t',1);mode,kind,oid=fields.decode().split();assert kind=='blob';result[path.decode()]=(mode,oid)
 return result
current=tree(C,HEAD);prior=tree(old,P);assert len(current)==len(prior)==204 and set(current)==set(prior)
changed=git(C,'diff-tree','--no-commit-id','--name-only','-r',P,HEAD).decode().splitlines()
expected=['fixture_tools/capsule_builder01.py','fixture_tools/generate_inputs01.py','proof_tools/build_release_draft01.py'];assert changed==expected,changed
assert not git(C,'diff','--name-only') and not git(C,'diff','--cached','--name-only')
rows=v['source_entries'];assert len(rows)==199 and sum(x['package_source'] for x in rows)==148
assert sum(x['bytes'] for x in rows)==3351623
for row in rows:
 name=row['target'];b=(C/name).read_bytes();assert b==(R/row['origin']).read_bytes()==git(C,'show',HEAD+':'+name)
 assert h(b)==row['sha256'] and len(b)==row['bytes'] and row['actual_git_commit']==HEAD
 assert current[name][0]=='100644' and stat.S_ISREG((C/name).lstat().st_mode)
 if row['package_source']:assert git(C,'show',A+':'+name)==b and name.startswith('tradingagents/')
 if name not in changed:assert b==(old/name).read_bytes()==git(old,'show',P+':'+name)
for name in prior:
 assert (old/name).read_bytes()==git(old,'show',P+':'+name)
aux=set(current)-{x['target'] for x in rows};assert len(aux)==5
for name in aux:assert (C/name).read_bytes()==git(C,'show',HEAD+':'+name)==git(C,'show',O+':'+name)
accepted=F/'held-consumer-fixture-successor-review02-2026-10-03/REVIEW_FIXTURE02.md'
assert h(accepted.read_bytes()).startswith('935a7f6e')

catalog=doc(R/q['source_catalog']);assert len(q['rows'])==q['count']==22 and q['logical_bytes']==961506
base=F/'original-import-native-successor-preparation06-2026-10-03'
archive=base/'outcome-recovery01/retained-primary01.tar.gz';assert h(archive.read_bytes())==catalog['archive_sha256']=='5f7d187b6320c7da55d7c47a87757bddcd03e093729cf4ed8f09cfe35cf3e6f1'
ret=doc(base/'RETAINED_PRIMARY01.json');originalmembers={x['path']:x for x in ret['members']}
catalogrows={x['name']:x for x in catalog['selected_bodies']};assert len(catalogrows)==22
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getmembers();assert len(members)==1058 and len({x.name for x in members})==1058
 by={x.name:x for x in members}
 for row in q['rows']:
  expectedrow=catalogrows[row['name']];assert {k:x for k,x in row.items() if k not in ('actual_copy','arrays_decoded')}==expectedrow
  body=Path(row['actual_copy']).read_bytes();assert Path(row['actual_copy'])==C/row['path']
  assert body==Path(row['original_path']).read_bytes()==Path(row['recovered_path']).read_bytes()
  assert h(body)==row['sha256'] and len(body)==row['bytes']
  tm=by['capsule04/'+row['path']];assert tm.isfile() and tm.size==row['bytes'] and tm.mode==row['mode']==originalmembers[row['path']]['mode']
  with tf.extractfile(tm) as f:assert f.read(1048577)==body
  for p in (Path(row['actual_copy']),Path(row['original_path']),Path(row['recovered_path'])):
   s=p.lstat();assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==row['mode'] and not p.is_symlink()
assert sum(x['bytes'] for x in q['rows'])==961506
inputpaths={x['path'] for x in q['rows']};assert len(inputpaths)==22
untracked=set(git(C,'ls-files','--others','--exclude-standard','-z').decode().strip('\0').split('\0'));assert untracked==inputpaths
whole={x.relative_to(C).as_posix() for x in C.rglob('*') if x.is_file() and '.git' not in x.relative_to(C).parts};assert whole==set(current)|inputpaths
originals=[x for x in q['rows'] if x['path'].startswith('fixture_inputs/original/')];provenance=[x for x in q['rows'] if x['name']=='target_provenance'];assert len(originals)==11 and len(provenance)==1 and len(q['rows'])-len(originals)-len(provenance)==10
assert h((F/'held-target-input-reuse-review01-2026-10-03/REVIEW_REUSE01.md').read_bytes())==q['accepted_input_reuse_review_sha256']
out=dict(schema_version=1,decision='accepted_local_source03_and_opaque_input_integration_only',head=HEAD,parent=P,anchor=A,original_S2=O,tracked=204,source_count=199,package_count=148,source_bytes=3351623,changed_paths=changed,all_current_origins_and_Git_equal=True,original_source02_unchanged=True,auxiliary_unchanged=sorted(aux),input_count=22,input_bytes=961506,input_roles={'original':11,'target_components_and_manifests':10,'target_provenance':1},input_original_recovered_archive_copy_modes_equal=True,untracked_paths=sorted(untracked),source_composition_sha256=h(sb),input_collection_sha256=h(ib),array_decoding=False,source_execution=False,network=False,qualification='Local integration and opaque prior-byte copy only; no source03 external retention, borrowed original objects, runtime, case, finite allocation, gate, claim or native authority inferred.')
(D/'READBACK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
