from pathlib import Path
F=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources');O=F/'financial-genuine-wrapper-claimedrun-final-capture-review01-2026-10-04'
s=(F/'financial-genuine-wrapper-claimedrun-witness-capture-review01-2026-10-04/check02.py').read_text()
s=s.replace("financial-genuine-wrapper-claimedrun-witness-capture-preparation01-2026-10-04","financial-genuine-wrapper-claimedrun-final-capture-preparation01-2026-10-04").replace('e4ee138df24ab2ce90c105fceb294ceb0749b2a541f7541b73afea723032d7cb','1c74338bb78018c8816933c23b850090ef29ebce503ef7420d716e1f2a374749').replace('13273cfa4436f9a687e18a9bb48a58eb3a4cfbfeed14ed37d45a11e919b88b2b','2991332ff476f776bd0b4aa12c3b3319647a4771352f1b8656a2398aba8f4c26').replace('fixed Root-installed capture scope','fixed Root-installed final capture')
a=s.index("census=F/");b=s.index("# Exact source suffix",a)
s=s[:a]+'''total=0;links=[];counts=[];fullscopes=[]
for scope,root in ns['SCOPES'].items():
 ck(root.resolve()==root,'actual closed root canonical');seen=[]
 def walk(p,n):
  global total
  st=p.lstat();r={'path':n,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISDIR(st.st_mode):r['kind']='directory';seen.append(r);[walk(c,c.name if n=='.' else n+'/'+c.name) for c in sorted(p.iterdir(),key=lambda p:p.name)]
  elif stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p));seen.append(r);links.append({'scope':scope,**r})
  else:b=read(p);ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'actual regular owned original');r.update(kind='file',bytes=len(b),sha256=sha(b));seen.append(r);total+=len(b)
 walk(root,'.');seen.sort(key=lambda r:r['path']);fullscopes.append({'scope':scope,'original_root':str(root),'members':seen});counts.append({'scope':scope,'root':str(root),'members_including_root':len(seen),'regular':sum(r['kind']=='file' for r in seen)})
ck(len(counts)==20 and len(links)==50 and sum(r['regular'] for r in counts)==1185 and total==18864635 and total<=ns['LIMIT'],'actual complete20/1185/50/logicalscope');(O/'ACTUAL_ORIGINAL_SCOPES01.json').write_text(json.dumps(fullscopes,sort_keys=True,indent=2)+'\\n')
capture=ns['SOURCE_CAPTURE'];ck(sha(read(capture/'source.tar.gz'))=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24','actual source archive');ck(sha(read(capture/'source-manifest.json'))=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8','actual source manifest');R.same(ns['SOURCE'],json.loads(read(capture/'source-manifest.json')))
ck(sha(read(ns['PARENT']/'REQUEST_FINAL03.json'))=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','actual final boundrequest');ck(sha(read(ns['PARENT']/'proofs/FULL_SOURCE_RECOVERY01.json'))=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','actual fullSource recoveryproof');ck(sha(read(ns['SCOPES']['actual-verifier-review']/'MANIFEST01.json'))=='0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2','actual binding independent review');ck(not os.path.lexists(ns['PARENT']/'attempt'),'actual Parent noattempt')
q=json.loads(read(ns['PARENT']/'REQUEST_FINAL03.json'));ck(sha(read(Path(q['final_review']['path'])))==q['final_review']['sha256']=='95dadb68b74693212dece8b363156ddc5d98c4b4726a9c50577d2655bb8f3c38','actual released contract review');ck(q['caller_sha256']==sha(read(ns['PARENT']/'parent01.py'))=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','actual Parent body')
for role,ref in q['proofs'].items():ck(sha(read(Path(ref['path'])))==ref['sha256'],'actual three proof bytes')
''' + s[b:]
s=s.replace('for i in range(4):','for i in range(20 if label==\'valid\' else 4):').replace("mapping['source_full_recovery_readback_sha256'] is None and len(mapping['scope_trees'])==4","mapping['source_full_recovery_readback_sha256']=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825' and len(mapping['scope_trees'])==20").replace("'no inherited recovery authority'","'exact sourcefullrecovery annotation and20tree projection'")
s=s.replace("'ACCEPTED_FOUR_HANDOFF_WITNESS_CAPTURE_SOURCE_ONLY'","'ACCEPTED_EXACT_FINAL20_TREE_CAPTURE_SOURCE_ONLY'").replace("'source_full_recovery':None","'source_full_recovery':'468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825'")
# End scan authenticates full actual memberships again; literal links never followed.
pos=s.index("ck(not os.path.lexists(ns['HERE']),'Root capture never executed')")
s=s[:pos]+'''for tree in fullscopes:
 root=Path(tree['original_root']);ck({'.'}|{p.relative_to(root).as_posix() for p in root.rglob('*')}=={r['path'] for r in tree['members']},'complete actualscope finalmembership')
 for row in tree['members']:
  p=root/row['path'];st=p.lstat();ck(stat.S_IMODE(st.st_mode)==row['mode'],'actual original finalmode')
  if row['kind']=='file':ck(sha(read(p))==row['sha256'],'actual original finalbody')
  elif row['kind']=='lexical-symlink':ck(os.readlink(p)==row['target'],'actual final literal target')
''' +s[pos:]
(O/'check01.py').write_text(s)
