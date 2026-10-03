"""Read-only selected input reuse audit. NPY and original sample JSON are opaque bytes."""
import hashlib,json,os,pathlib,stat,subprocess,tarfile
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FULL=HERE.parent
PREP=FULL/'original-import-native-successor-preparation06-2026-10-03'
CAP=PREP/'capsule04'
REC=PREP/'outcome-recovery01/recovered-terminal-capsule04'
BARE=PREP/'outcome-recovery01/repository.git'
LIMIT=4*1024**2
pins={}
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 p=pathlib.Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=LIMIT
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);parts=[];primary=None
 try:
  assert signature(os.fstat(fd))==signature(before)
  total=0
  while True:
   b=os.read(fd,min(65536,before.st_size-total+1))
   if not b:break
   total+=len(b);assert total<=before.st_size;parts.append(b)
  assert signature(os.fstat(fd))==signature(before) and signature(p.lstat())==signature(before)
 except BaseException as e:primary=e
 try:os.close(fd)
 except BaseException as e:
  if primary is None or isinstance(e,(MemoryError,KeyboardInterrupt,SystemExit)) and not isinstance(primary,(MemoryError,KeyboardInterrupt,SystemExit)):primary=e
 if primary is not None:raise primary
 b=b''.join(parts);pins[str(p)]={'sha256':sha(b),'bytes':len(b)};return b
# atime changes are excluded from stable identity; reads cannot change mtime/size/inode.
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
# Normalize stat equality used above to the explicit stable signature in the read helper.
def doc(p):return json.loads(raw(p))
def git(repo,*args):
 env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_ALLOW_PROTOCOL':''}
 return subprocess.run(['git','-c','protocol.allow=never','-C',str(repo),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=10).stdout
def obj(repo,ref):
 assert int(git(repo,'cat-file','-s',ref))<=LIMIT
 assert git(repo,'cat-file','-t',ref).strip()==b'blob'
 return git(repo,'cat-file','blob',ref)
def save(name,x):
 with (HERE/name).open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
def ref(path):
 b=raw(CAP/path);return {'path':path,'sha256':sha(b),'bytes':len(b)}
def main():
 recovery=doc(PREP/'REMOTE_PRIMARY_RECOVERY01.json');retention=doc(PREP/'RETAINED_PRIMARY01.json');release=doc(PREP/'release01.json')
 indexpath=FULL/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json';index=doc(indexpath)
 review=FULL/'original-import-native-timeout-recovery-review04-2026-10-03'
 for name in ('REVIEW_RECOVERY04.md','MANIFEST01.json','readback04.json'):raw(review/name)
 assert git(BARE,'rev-parse','FETCH_HEAD').decode().strip()==recovery['remote_commit']
 remote=[]
 for r in recovery['selected_blobs']:
  b=obj(BARE,recovery['remote_commit']+':'+r['path']);assert sha(b)==r['sha256'] and len(b)==r['bytes'];remote.append(r)
 assert len(remote)==52
 for p in (indexpath,PREP/'release01.json',PREP/'RETAINED_PRIMARY01.json'):
  r=next(r for r in remote if r['path']==str(p.relative_to(ROOT)));assert sha(raw(p))==r['sha256']
 archive=PREP/'outcome-recovery01/retained-primary01.tar.gz';assert sha(raw(archive))==recovery['archive_sha256']==retention['archive_sha256']
 assert any(r['sha256']==recovery['archive_sha256'] for r in remote)
 members={r['path']:r for r in retention['members']};assert len(members)==1058
 cases=release['cases']['success'];inputs=cases['experiment']['inputs']
 control=doc(CAP/inputs['original_import']['path']);assert sha(raw(CAP/inputs['original_import']['path']))==inputs['original_import']['sha256']
 assert (control['sample_count'],control['motif_count'])==(512,32)
 selected={n:r for n,r in inputs.items() if n.startswith('target_') or r['path'].startswith('fixture_inputs/original/')};assert len(selected)==22
 checked=[]
 with tarfile.open(archive,'r:gz') as tar:
  tm={m.name:m for m in tar.getmembers()};assert len(tm)==1058
  for n,r in sorted(selected.items()):
   a=raw(CAP/r['path']);b=raw(REC/r['path']);m=members[r['path']];t=tm['capsule04/'+r['path']]
   assert a==b and sha(a)==r['sha256']==m['sha256'] and len(a)==m['bytes']==t.size
   assert stat.S_IMODE((CAP/r['path']).lstat().st_mode)==stat.S_IMODE((REC/r['path']).lstat().st_mode)==m['mode']==t.mode
   assert t.isfile() and t.size<=LIMIT
   with tar.extractfile(t) as stream:assert stream.read(LIMIT+1)==a
   checked.append({'name':n,**ref(r['path']),'mode':m['mode'],'original_path':str(CAP/r['path']),'recovered_path':str(REC/r['path'])})
 original=[]
 for r in index['inputs']:
  name=next(n for n,v in selected.items() if v['path']==r['capsule_path']);v=ref(r['capsule_path']);assert v['sha256']==r['sha256'] and v['bytes']==r['bytes']
  original.append({'name':name,'reference':v,'original_path':r['original_path']})
 assert len(original)==11 and sum(x['reference']['bytes'] for x in original)==957811
 source_objects=[]
 for path,v in sorted(index['original_source_files'].items()):
  a=obj(CAP,index['original_source']+':'+path);b=obj(REC,index['original_source']+':'+path);assert a==b and sha(a)==v['sha256']==v['claim_sha256'];source_objects.append({'path':path,'sha256':sha(a),'bytes':len(a)})
 assert len(source_objects)==26
 targets=[]
 provenance=doc(CAP/inputs['target_provenance']['path'])
 assert provenance=={'generator':'registered-explicit-arrays-v1','kind':'synthetic-original-import-targets','node_denominators':[2,3],'schema_version':1}
 for target in cases['targets']:
  name=next(n for n,r in inputs.items() if r['path']==target['manifest']);m=doc(CAP/target['manifest']);assert m['graph_hash']==target['graph_hash'] and m['metadata']['source_hashes']==[inputs['target_provenance']['sha256']]
  components={}
  for n,r in m['arrays'].items():
   v=ref(str(pathlib.PurePosixPath(target['manifest']).parent/r['path']));assert v['sha256']==r['sha256'] and v['bytes']==r['bytes'] and inputs[name+'_'+n]['sha256']==v['sha256'];components[n]=v
  targets.append({'graph_hash':target['graph_hash'],'nodes':target['nodes'],'input_name':name,'manifest':ref(target['manifest']),'components':components})
 assert [t['graph_hash'] for t in targets]==sorted({t['graph_hash'] for t in targets}) and [t['nodes'] for t in targets]==[2,3]
 histories=[]
 for i in range(1,5):
  ident='original-import-native-success-20261003-%02d'%i;cp='research_runs/'+ident+'/claim.json';fp='research_runs/'+ident+'/failed.json';claim=doc(CAP/cp);failed=doc(CAP/fp)
  for path in (cp,fp):assert raw(CAP/path)==raw(REC/path) and sha(raw(CAP/path))==members[path]['sha256']
  for n,r in selected.items():assert claim['inputs'][n]==r
  registration=obj(REC,claim['source']+':'+claim['registration']);assert sha(registration)==claim['registration_sha256']
  reg=json.loads(registration);assert reg['experiments'][ident]['inputs']==claim['inputs']
  generator=obj(REC,claim['source']+':fixture_tools/generate_inputs01.py');assert sha(generator)==reg['experiments'][ident]['source_files']['fixture_tools/generate_inputs01.py']
  histories.append({'identity':ident,'source':claim['source'],'claim':ref(cp),'terminal':ref(fp),'registration_sha256':sha(registration),'generator_sha256':sha(generator),'generator_bytes':len(generator),'effective_attempt_budget':claim['effective_attempt_budget'],'datasets':reg['datasets']})
 assert histories[-1]['claim']['sha256']==recovery['claim_sha256']
 save('TARGET_CATALOG01.json',{'schema_version':1,'kind':'registered-imported-held-targets-v1','targets':targets})
 save('ORIGINAL_IMPORT_INDEX_ROLE01.json',{'original_source':index['original_source'],'original_claim':index['original_claim'],'inputs':original})
 save('ORIGINAL_EVIDENCE_ROLE01.json',{'sample_count':512,'motif_count':32,'resample':False,'recluster':False,'original_source':index['original_source'],'original_claim':index['original_claim'],'dictionary_identity':index['dictionary_identity'],'dictionary_component':index['dictionary_component'],'parent_terminal':index['parent_terminal'],'control_reference':ref(inputs['original_import']['path']),'qualification':'Derived metadata for prospective import; no new authority or semantic sample revalidation.'})
 save('TARGET_PROVENANCE_ROLE01.json',{'name':'target_provenance','dataset':'synthetic','reference':ref(inputs['target_provenance']['path']),'document':provenance})
 save('READBACK01.json',{'status':'selected-input-reuse-bytes-verified','remote_commit':recovery['remote_commit'],'remote_blob_count':len(remote),'archive_sha256':recovery['archive_sha256'],'archive_members':len(members),'selected_bodies':checked,'original_source_objects':source_objects,'historical_failed_claims':histories,'current_completed_mcm_targets':recovery['completed_mcm_targets'],'node_count_authority':'Historical registered release target list/provenance; NPY shapes were not parsed.','execution_admitted':False,'inputs_copied':False,'arrays_decoded':False})
 save('SOURCE_REFERENCES01.json',pins)
 print(json.dumps({'status':'PASS','selected_input_files':len(checked),'original_json_bytes':957811,'original_source_objects':26,'remote_git_blobs':52,'historical_failed_claims':4,'target_graphs':targets,'execution_admitted':False},sort_keys=True))
if __name__=='__main__':main()
