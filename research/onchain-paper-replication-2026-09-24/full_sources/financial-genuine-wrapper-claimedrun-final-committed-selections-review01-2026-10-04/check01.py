import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];C=B/'financial-genuine-wrapper-claimedrun-final-selected-closure-census02-2026-10-04';PR=B/'financial-genuine-wrapper-claimedrun-final-selected-closure-review02-2026-10-04';COMMIT='a9b219042109be78498185cc6539c1454736e3eb';count=0;gitcalls=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,n):
 global count
 assert v,n;count+=1
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and p.resolve()==p and s.st_size<=4194304,'ordinary stable selected path');b=p.read_bytes();e=p.lstat();ck((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(e.st_dev,e.st_ino,e.st_mode,e.st_size,e.st_mtime_ns,e.st_ctime_ns),'stable read');return b
def doc(p,pin):
 b=read(p);ck(sha(b)==pin,'metadata exact pin');return json.loads(b)
proof=doc(PR/'MACHINE01.json','064d78d560dbdee69d829e67bcc6390d20d0ee9a3dca18f6b9f4bbc621ca9ab5');doc(PR/'MANIFEST01.json','542c14e4f8afe7bc7eb08416f7406746f01b38ce7ffee3708ab01fc6776ccf6d');batches=doc(C/'TRANSPORT_BATCHES02.json','8f3e9ef773fdd9d2a815b3133bd28297930d02043182a4f4a8c68d982159f095')['batches'];census=doc(C/'CANDIDATE_ROWS02.json','70ff2feb00e4d334a14897a87222077b943643d96bff087a275bbcdd3b43569f')['rows'];allrows={r['path']:r for r in census};selected=[];roots=[];pins=['28f95d42e6f53c243d31ed9867724fedd89b04cb601b63de199ac2616c0f49c9','c8dd51669514a49a1c75ad6e74572579d1a0590bad8c1da0d44d70245c54c4ea']
for i,base in enumerate(['financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04','financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04']):
 root=B/base;roots.append(root);q=doc(root/'SELECTED_BODIES01.json',pins[i]);source=read(root/'recover01.py');ck(sha(source)=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','unchanged accepted transport');ns={'__name__':'source_validation_only','__file__':str(root/'recover01.py')};exec(compile(source,'exact transport definitions','exec'),ns);ns['validate_fixed_selection'](q);ck(ns['encode'](q)==read(root/'SELECTED_BODIES01.json'),'exact canonical schema');ck(q['remote_commit']==COMMIT,'one immutable commit');expected=[{k:r[k] for k in ('path','bytes','sha256')} for r in batches[i]['rows']];ck(q['rows']==expected,'exact accepted candidate role projection');ck([r['path'] for r in q['rows']]==sorted({r['path'] for r in q['rows']}),'sorted unique');ck(len(q['rows'])<=506 and sum(r['bytes'] for r in q['rows'])<=67108864 and max(r['bytes'] for r in q['rows'])<=4194304 and 11+2*len(q['rows'])<=1024,'all effective finite limits')
 for name in ['fresh-recordfix-source325-01.git','selected','INTENT01.json','REMOTE_RECOVERY01.json','FAILED01.json']:ck(not os.path.lexists(root/name),'fresh actual namespace')
 selected.append(q)
sets=[{r['path'] for r in q['rows']} for q in selected];ck(sets[0]|sets[1]==set(allrows) and sets[0]&sets[1]==set(batches[0]['mandatory_shared_anchors']) and len(sets[0]&sets[1])==6,'689 complete only6 overlap')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
def git(args,data=None):
 global gitcalls
 p=subprocess.run(['git','-c','protocol.allow=never',*args],cwd=MAIN,env=env,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);gitcalls+=1;ck(p.returncode==0 and len(p.stdout)<=8*1024**2 and len(p.stderr)<=65536,'bounded local immutable Git');return p.stdout
ck(git(['rev-parse','HEAD']).decode().strip()==COMMIT,'actual current Main commit');ck(git(['cat-file','-t',COMMIT])==b'commit\n','real commit object')
raw=git(['ls-tree','-r','-z',COMMIT,'--',*sorted(allrows)]);entries={}
for line in raw.split(b'\0'):
 if not line:continue
 head,name=line.split(b'\t',1);mode,kind,oid=head.decode().split();name=name.decode();ck(kind=='blob' and mode in ('100644','100755') and name not in entries,'real regular tracked mode');entries[name]=(mode,oid)
ck(set(entries)==set(allrows),'every selected path in exact committed tree');oids={}
for name,r in allrows.items():
 body=read(MAIN/name);st=(MAIN/name).lstat();mode,oid=entries[name];ck(len(body)==r['bytes'] and sha(body)==r['sha256'] and stat.S_IMODE(st.st_mode)==r['mode'],'current body/mode equals accepted census');ck(mode==('100755' if r['mode']&0o111 else '100644') and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'literal mode versus Gitmode and actual blobOID');oids.setdefault(oid,[]).append(name)
# Batched immutable reads capped below8MiB; no local Git mutation or network.
items=list(oids);batches_oid=[];batch=[];size=0
for oid in items:
 n=allrows[oids[oid][0]]['bytes']+128
 if batch and size+n>6*1024**2:batches_oid.append(batch);batch=[];size=0
 batch.append(oid);size+=n
if batch:batches_oid.append(batch)
for group in batches_oid:
 raw=git(['cat-file','--batch'],(''.join(o+'\n' for o in group)).encode());off=0
 for oid in group:
  end=raw.index(b'\n',off);got,kind,n=raw[off:end].decode().split();n=int(n);ck(got==oid and kind=='blob' and n<=4194304,'exact immutable blob header');body=raw[end+1:end+1+n];ck(raw[end+1+n:end+2+n]==b'\n','exact batch framing');off=end+2+n
  for name in oids[oid]:r=allrows[name];ck(len(body)==r['bytes'] and sha(body)==r['sha256'] and body==read(MAIN/name),'every committed blob equals actual row')
 ck(off==len(raw),'no extra Git output')
# Original closure metadata is unchanged: proof covers canonical archive/source scope; exact blobs now bind it.
for name in ['COMPLETE_TYPED_ROOTS02.json','ACTUAL_HELPER_REVIEW_BINDING01.json','census02.py']:ck(str((C/name).relative_to(MAIN)) in allrows,'committed complete typed/role binding selected')
for root,q in zip(roots,selected):ck(read(root/'SELECTED_BODIES01.json')==ns['encode'](q),'selection unchanged after Git joins')
ck(git(['rev-parse','HEAD']).decode().strip()==COMMIT,'Main HEAD unchanged after proof')
out={'schema_version':1,'decision':'accepted-exact-two-committed-byte-transport-selections','commit':COMMIT,'selection_sha256':{'primary':pins[0],'supplemental':pins[1]},'candidate_scope_review_sha256':'064d78d560dbdee69d829e67bcc6390d20d0ee9a3dca18f6b9f4bbc621ca9ab5','distinct_paths':689,'distinct_bytes':52795748,'primary':{'paths':359,'bytes':52374727,'maximum_git_operations':729},'supplemental':{'paths':336,'bytes':4362239,'maximum_git_operations':683},'shared_safety_anchor_paths':6,'immutable_unique_blob_objects':len(oids),'bounded_local_git_calls':gitcalls,'checks':count,'fresh_both_namespaces':True,'actual_remote_readback_observed_by_this_review':False,'actual_transfer_performed':False,'numerical_authority':False,'qualification':'Exact source and local immutable committed-body selection acceptance permits one original ordinary byte transport per namespace after Root actual remote confirmation. Both actual outcomes and complete recovery remain separately required. Shared anchors do not transfer numerical identity/budget.'}
(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');(H/'COMMITTED_BLOBS01.json').write_text(json.dumps({n:{'mode':m,'oid':o} for n,(m,o) in sorted(entries.items())},sort_keys=True,indent=2)+'\n');print('PASS',count,'Gitcalls',gitcalls)
