import copy,gzip,hashlib,importlib,io,json,os,shutil,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];role=sys.argv[1];assert role in ('FINAL11','WITNESS57');root=B/('financial-genuine-wrapper-root-claimedrun-final-sharded-flat01-2026-10-04' if role=='FINAL11' else 'financial-genuine-wrapper-root-claimedrun-witness-sharded-flat01-2026-10-04');module='restore_sharded01' if role=='FINAL11' else 'restore_witness01';sys.path.insert(0,str(root));M=importlib.import_module(module);R=M.R;count=0;failures=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,n):
 global count
 assert v,n;count+=1
def refuse(fn,n):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError) as e:failures.append({'control':n,'exception':type(e).__name__,'message':str(e)});ck(True,n)
 else:raise AssertionError('not refused '+n)
def doc(p,pin=None):
 b=R.read(p.parent,p.name);ck(pin is None or sha(b)==pin,'exact input pin');return json.loads(b)
expectedq='87af86151a287e8e6f28e086eb30c84b56a291be94049afbc3a3f8951f166ff0' if role=='FINAL11' else 'd599a6cdee11b6fbca074ec3cab3b246437a2c7d45429e150a6e7c3e2d48ec9d';expectedcontract='839a13bdfe6df92c4b0b641111f98bb3fb34526913c3c760783be186bee8befc' if role=='FINAL11' else '8bbe2be217a75a13fcc971bf66f84a924bdeae11ca5779cae5517a34986fcc4f';helper='f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7' if role=='FINAL11' else '5352c2e42d11d585e92187f2d51be9c42eaadcfc9b03f8e11e9a7097bf7c28ac';review='f730a0b30f8fe5aa1ac1c0f389f75eadba789f61e46d8994c715aadf008db1c5' if role=='FINAL11' else 'fe47a1fcdd3dd9f9787556a15311808a57f7cbf0d70b92d958cbc39b7f3a6475'
q=doc(root/'REQUEST_BOUND_DRAFT02.json',expectedq);ck(q['release'] is None and M.contract(q)==expectedcontract,'genuine unresolved draft exact contract');ck(sha(R.read(root,module+'.py'))==helper,'installed caller exact source');ck(sha(M.reference(q['review']))==review,'genuine source reviewer body');refuse(lambda:M.request(q),'unreleased original draft')
proof=B/'financial-genuine-wrapper-claimedrun-final-actual-two-batch-remote-review01-2026-10-04';doc(proof/'MACHINE01.json','236918fc76a2ce7119a4ac959b2398e849307528a9ede73566328571626c501f');doc(proof/'MANIFEST01.json','ef5d56545b20e89ef9c4311fbbfe0f1f6f4950d872978f294b4a01a9ddf8c1c5');ck(q['remote_commit']=='a9b219042109be78498185cc6539c1454736e3eb' and q['remote_receipt_sha256']=='ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440','actual primary remote binding');remote=Path(q['remote_root']);out=Path(q['output_root']);ck(not os.path.lexists(out) and out.parent==B and out.resolve()==out,'actual fresh canonical output');ck(shutil.disk_usage(B).free>=10737418240,'current actual10GiBfloor')
refs=[q[k] for k in (('manifest','shard_index','union_auth') if role=='FINAL11' else ('manifest','shard_index','union_auth','direct_body'))];bodies=M.selected(remote,q,refs);m=M.manifest_join(q,bodies[q['manifest']['path']]);index,plans,extra=M.validate_index(q,m,bodies[q['shard_index']['path']]);allrefs=refs+extra;allb=M.selected(remote,q,allrefs);ck(len(allrefs)<=506 and sum(r['bytes'] for r in allrefs)<=64*1024**2,'actual complete selected ref caps');mapping=None;globalfiles={};prefix=Path(q['shard_index']['path']).parent
for row,plan in zip(index['shards'],plans):
 mf=plan['manifest'];ck(allb[str(prefix/row['manifest']['path'])]==R.encode(mf),'every actual manifest byte');raw=allb[str(prefix/row['archive']['path'])];frames=list(R.framed_members(raw));ck(len(frames)==len(mf['members']),'complete bounded footer frames');bb={}
 for (name,t,b),r in zip(frames,mf['members']):
  ck(name==r['path'] and t.mode==r['mode'] and ((t.isdir() and not b) if r['kind']=='directory' else (t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256'])),'every current fullarchive original body');bb[name]=b
  if r['kind']=='file':ck(name not in globalfiles,'disjoint full file partition');globalfiles[name]=(len(b),sha(b))
 encoded=io.BytesIO()
 with gzip.GzipFile(fileobj=encoded,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for r in mf['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=t.mtime=0;t.uname=t.gname=''
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;tf.addfile(t)
    else:t.size=len(bb[r['path']]);tf.addfile(t,io.BytesIO(bb[r['path']]))
 ck(encoded.getvalue()==raw,'exact actual entire canonical compressed archive')
 if 'ORIGINAL_TREES01.json' in bb:mapping=bb['ORIGINAL_TREES01.json']
ck(set(globalfiles)=={r['path'] for r in m['members'] if r['kind']=='file'},'complete global fullscope');summary=M.authenticate_union(q,m,index,allb[q['union_auth']['path']],mapping);trees=json.loads(mapping)['scope_trees'];M.validate_expected_trees(trees)
for tree in trees:
 original=Path(tree['original_root']);actual=[]
 def visit(p,n):
  t=p.lstat();r={'path':n,'mode':stat.S_IMODE(t.st_mode)}
  if stat.S_ISLNK(t.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(t.st_mode):
   r['kind']='directory';actual.append(r)
   for c in sorted(p.iterdir()):visit(c,c.name if n=='.' else n+'/'+c.name)
   return
  else:
   ck(stat.S_ISREG(t.st_mode) and t.st_nlink==1,'current original regular identity');b=R.read(original,n);r.update(kind='file',bytes=len(b),sha256=sha(b))
  actual.append(r)
 visit(original,'.');actual.sort(key=lambda r:r['path']);wanted=[{k:v for k,v in r.items() if k not in ('union_path','direct_source_path')} for r in tree['members']];ck(actual==wanted,'entire current original census body/type/mode/link unchanged')
if role=='WITNESS57':
 direct=allb[q['direct_body']['path']];ck(len(direct)==2532973 and sha(direct)=='c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3','actual fetched sole direct raw');ck(sha(M.reference(q['framer_review']))=='64bc091e50fda054306df6ef7d966582b8a4580d5591049fe6cf409105503588','exact genuine framer proof copied');ck((MAIN/q['direct_body']['path']).lstat().st_mode&0o777==384,'original direct literal mode')
else:
 failed=B/'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04';ck(R.read(failed,'union-manifest.json')==bodies[q['manifest']['path']],'complete unchanged failed c720 identity');receipt=doc(remote/'REMOTE_RECOVERY01.json');present={r['path'] for r in receipt['selected_blobs']}
 for n in ['ACTUAL_CAPTURE01.err','ACTUAL_CAPTURE01.out','ACTUAL_TOOL_TERMINAL02.json','FAILED_SCOPE_MANIFEST03.json','ROOT_ADOPTION01.json','capture01.py','union-manifest.json','union.tar.gz']:ck(str((failed/n).relative_to(MAIN)) in present,'original failed outside8 retained remote')
source=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');cap=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';sm=doc(cap/'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8');R.same(source,sm);parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01');ck(sha(R.read(parent,'REQUEST_FINAL03.json'))=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8' and not (parent/'attempt').exists(),'current final caller/noattempt');ck(M.selected(remote,q,allrefs)==allb,'actual selected body chain unchanged after checks')
# Independent exact releases are authored only after real predicates pass.
release={'schema_version':1,'decision':'accepted-exact-one-use-final-union-sharded-flat' if role=='FINAL11' else 'accepted-exact-one-use-witness-sharded-plus-direct-flat','contract_sha256':expectedcontract,'helper_sha256':helper,'review_sha256':review};p=H/(role+'_RELEASE01.json');raw=R.encode(release)
with p.open('xb') as f:f.write(raw)
bound=copy.deepcopy(q);bound['release']={'path':str(p),'sha256':sha(raw)};ck(M.request(bound)==(remote,out) and M.contract(bound)==expectedcontract,'genuine release actual pure request validation')
for key,val in [('remote_commit','0'*40),('expected_files',q['expected_files']-1),('output_root',str(out)+'-other')]:
 bad=copy.deepcopy(bound);bad[key]=val;refuse(lambda:M.request(bad),'bound tamper '+key)
result={'schema_version':1,'decision':'accepted-exact-flat-contract-release','role':role,'original_request_sha256':expectedq,'contract_sha256':expectedcontract,'helper_sha256':helper,'source_review_sha256':review,'release_sha256':sha(raw),'remote_receipt_sha256':q['remote_receipt_sha256'],'actual_remote_review_sha256':'236918fc76a2ce7119a4ac959b2398e849307528a9ede73566328571626c501f','checks':count,'summary':summary,'refusals':failures,'fresh_output':str(out),'actual_restore':False,'numerical_authority':False}
with (H/(role+'_READBACK01.json')).open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
with (H/(role+'_ORIGINAL_DRAFT02.json')).open('xb') as f:f.write(R.read(root,'REQUEST_BOUND_DRAFT02.json'))
print(role,'PASS',count,'release',sha(raw))
