from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parent;old=(B/'recipe01.py').read_text();edits=[]
helpers='''def _git_environment():
 return {**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull}

def _git_bytes(root,*args):
 raw=subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL,timeout=10,env=_git_environment())
 require(len(raw)<=1024**2,'bounded source Git metadata exceeded')
 return raw

def _git_status(root,*args):
 result=subprocess.run(['git',*args],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,env=_git_environment())
 require(result.returncode in (0,1),'source Git comparison failed')
 return result.returncode

def _git_tree(root,commit,expected):
 require(type(commit)is str and re.fullmatch('[0-9a-f]{40}',commit) is not None and 0<len(expected)<=160,'finite committed source map required')
 for rel in expected:
  path=Path(rel);require(type(rel)is str and not path.is_absolute() and str(path)==rel and '..' not in path.parts and not any(c in rel for c in ('\\0','\\n','\\r','\\t')) and all(p not in PROTECTED for p in path.parts),'unsafe committed source path')
 raw=_git_bytes(root,'--literal-pathspecs','ls-tree','-z',commit,'--',*sorted(expected));actual={}
 for row in raw.split(b'\\0'):
  if not row:continue
  header,path=row.split(b'\\t',1);mode,kind,oid=header.decode().split(' ');rel=path.decode()
  require(rel not in actual,'duplicate committed source path');actual[rel]={'git_mode':mode,'git_blob_oid':oid,'kind':kind}
 require(set(actual)==set(expected),'committed source membership differs')
 for rel,pin in expected.items():
  require(actual[rel]=={'git_mode':pin['git_mode'],'git_blob_oid':pin['git_blob_oid'],'kind':'blob'},'committed source body/type/mode differs')
 return actual

def verify_current_main(root,base,guards):
 """Source identity, not HEAD equality; no authority and no checkout mutation."""
 require(base['root']==str(root) and base['source_count']==135 and len(base['sources'])==135,'exact historical baseline required')
 verify_source(root,base['sources'])
 head=_git_bytes(root,'rev-parse','--verify','HEAD').decode().strip()
 _git_tree(root,base['head'],base['sources']);_git_tree(root,head,base['sources'])
 require(_git_status(root,'merge-base','--is-ancestor',base['head'],head)==0,'current Main must descend from historical baseline')
 # Only documentation/evidence trees may change outside the immutable source map.
 # Research source snapshots are evidence, not installed implementation bodies.
 require(_git_status(root,'diff','--quiet','--no-ext-diff','--no-textconv',base['head'],head,'--','.',':(exclude)docs/**',':(exclude)research/**')==0,'non-documentation/evidence commit delta refused')
 guard_tree={}
 for rel,pin in guards.items():
  raw=bounded(root/rel);mode=stat.S_IMODE((root/rel).stat().st_mode)
  require(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'] and mode==pin['mode'],'original scientific configuration/protocol changed')
  guard_tree[rel]={'git_blob_oid':blob(raw),'git_mode':'100755' if mode&0o111 else '100644'}
 _git_tree(root,base['head'],guard_tree);_git_tree(root,head,guard_tree)
 verify_source(root,base['sources'])
 require(_git_bytes(root,'rev-parse','--verify','HEAD').decode().strip()==head,'Main changed during source verification')
 return {'root':str(root),'commit':head,'source_count':135,'historical_baseline_commit':base['head'],'historical_baseline_is_ancestor':True,'source_and_scientific_guards_equal':True,'permitted_changed_trees':['docs/','research/'],'authority':None}

'''
edits.append({'old':'def prepare(target,roles):','new':helpers+'def prepare(target,roles):'})
edits.append({'old':" head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN,text=True,timeout=10).strip();require(head==base['head'],'current Main commit differs; require a fresh explicit source recipe')\n verify_source(MAIN,base['sources']);verify_source(HERE/'candidate',candidate['sources'])",'new':" guards=document('SCIENTIFIC_GUARDS01.json','2a41ca2a003667553b870954df603e367285c198da6c5a13f1e465a744ebf21e')\n current=verify_current_main(MAIN,base,guards);head=current['commit']\n verify_source(HERE/'candidate',candidate['sources'])"})
edits.append({'old':" guards=document('SCIENTIFIC_GUARDS01.json','2a41ca2a003667553b870954df603e367285c198da6c5a13f1e465a744ebf21e')\n for rel,pin in guards.items():\n  raw=bounded(MAIN/rel);require(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'] and stat.S_IMODE((MAIN/rel).stat().st_mode)==pin['mode'],'original scientific configuration/protocol changed')\n",'new':''})
edits.append({'old':" require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN,text=True,timeout=10).strip()==head,'Main changed during preparation')",'new':" verify_source(MAIN,base['sources']);verify_source(HERE/'candidate',candidate['sources'])\n require(_git_bytes(MAIN,'rev-parse','--verify','HEAD').decode().strip()==head,'Main changed during preparation')"})
edits.append({'old':"'original_main':{'root':str(MAIN),'commit':head,'source_count':135},'candidate_source_count':138",'new':"'original_main':{'root':str(MAIN),'commit':base['head'],'source_count':135},'current_main':current,'candidate_source_count':138"})
new=old
for e in edits:
 assert new.count(e['old'])==1
 new=new.replace(e['old'],e['new'])
(B/'recipe02.py').write_text(new)
# The removed old guard block is restored at its exact neighboring source anchor.
reverse=[]
for e in edits:
 if e['new']:reverse.append(e)
 else:
  reverse.append({'old':e['old']+" copy=[",'new':" copy=["})
(B/'RECIPE_INVERSE01.json').write_text(json.dumps({'baseline_recipe_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_recipe_sha256':hashlib.sha256(new.encode()).hexdigest(),'edits':reverse,'scope':'new read-only current source/Git verification and distinct historical/current provenance; every other recipe/source/input/future-authority clause unchanged'},sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(new.encode()).hexdigest())
