import hashlib,importlib.metadata,json,os,sys
from pathlib import Path
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-root-launch-20261004-01');q=json.loads((P/'REQUEST_FINAL03.json').read_bytes());rows=q['runtime_mapping']['distribution_records'];observed=[]
for i,r in enumerate(rows):
 d=importlib.metadata.distribution(r['name']);matches=[str(f) for f in d.files or () if str(f).endswith('.dist-info/RECORD')]
 p=Path(r['record']);raw=p.read_bytes();assert len(raw)<=4*1024**2 and hashlib.sha256(raw).hexdigest()==r['record_sha256'] and d.version==r['version']
 if len(matches)!=1:observed.append({'row_index':i,'name':r['name'],'version':d.version,'record_matches':matches,'match_count':len(matches),'direct_pinned_RECORD_hash_matches':True})
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','tradingagents'} for n in sys.modules)
print(json.dumps({'schema_version':1,'cwd':os.getcwd(),'executable':sys.executable,'observation':'stdlib metadata only, actual source launch cwd; no execution or native claim','predicate_failures':observed,'first_observed_failure':observed[0],'numerical_imports':False},sort_keys=True,indent=2))
