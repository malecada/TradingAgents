from pathlib import Path
import json,hashlib,stat,re,os
from html.parser import HTMLParser
H=Path(__file__).resolve().parent;A=H.with_name('fund-cohort-historical-evidence-investigation01-2026-10-04');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,s):assert v,s;checks.append(s)
b=(A/'MANIFEST01.json').read_bytes();ok(sha(b)=='ee18d505bf55fee4c44370d8e90a2710b1f59a6218f2c48a9aaeca8f5c85629d','manifest pin');m=json.loads(b)['members'];ok(len(m)==33,'33 members');ok(sorted(['.']+[str(p.relative_to(A)) for p in A.rglob('*') if p!=A/'MANIFEST01.json'])==sorted(r['path'] for r in m),'complete scope')
for r in m:
 p=A/r['path'];s=p.lstat();mode=r['mode'];ok(stat.S_IMODE(s.st_mode)==(int(mode,8) if type(mode)is str else mode),'mode '+r['path']);
 if r['type']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory');continue
 ok(stat.S_ISREG(s.st_mode),'regular '+r['path']);b=p.read_bytes();ok(len(b)==r['size'] and sha(b)==r['sha256'],'body '+r['path'])
for p in A.glob('*.receipt.json'):
 v=json.loads(p.read_text())
 if 'sha256'in v:
  b=p.with_name(p.name.removesuffix('.receipt.json')).read_bytes();ok(sha(b)==v['sha256'] and len(b)==v['bytes'],'receipt '+p.name)
rb=json.loads((A/'READBACK01.json').read_text());tree=json.loads((A/'collector_tree.json').read_text());ok(tree['truncated'] is False,'untruncated tree');entries={v['path']:v for v in tree['tree']}
for j in rb['joins']:
 b=(A/j['local']).read_bytes();t=entries[j['path']];oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();ok(oid==t['sha']==j['git_blob_oid'] and t['mode']=='100644' and t['type']=='blob' and len(b)==t['size']==j['size'],'Git blob '+j['local'])
# Reject duplicate JSON keys, not merely duplicates after dict decoding.
def unique(pairs):
 d={}
 for k,v in pairs:ok(k not in d,'unique address '+k);d[k]=v
 return d
fund=json.loads((A/'historical_fund.json').read_text(),object_pairs_hook=unique);old=json.loads((A/'historical_fund_march.json').read_text(),object_pairs_hook=unique)
ok(len(fund)==65 and len(old)==64,'counts');ok(all(re.fullmatch('0x[0-9a-f]{40}',k) and type(v)is str for k,v in fund.items()),'address syntax');num=[int(v.rsplit(' ',1)[1]) for v in fund.values() if re.fullmatch('Alameda Research [0-9]+',v)];ok(sorted(num)==[i for i in range(1,28) if i not in (18,21)],'25 numbered labels');ok(sum(v.startswith('Alameda Research') for v in fund.values())==27,'27 including deposits');ok(set(fund)-set(old)=={'0xe11970f2f3de9d637fb786f2d869f8fea44195ac'} and all(fund[k]==v for k,v in old.items()),'only Amber added')
b=('\n'.join(sorted(fund))+'\n').encode();ok(b==(A/'ORDERED_ADDRESSES01.txt').read_bytes(),'exact address order');b=(json.dumps([{'address':a,'label':fund[a]} for a in sorted(fund)],sort_keys=True,separators=(',',':'))+'\n').encode();ok(b==(A/'ORDERED_MEMBERSHIP01.json').read_bytes(),'exact ordered labels')
hist=json.loads((A/'fund_history.json').read_text());ok([x['commit']['committer']['date'] for x in hist]==['2023-06-16T18:39:41Z','2023-03-26T09:53:26Z'],'June March history');j=json.loads((A/'fund_june_commit.json').read_text());ok(next(x for x in j['files'] if x['filename']=='data/etherscan/accounts/fund.json')['sha']==rb['joins'][0]['git_blob_oid'],'June own file blob');october=json.loads((A/'collector_commit.json').read_text())[0];ok(october['commit']['committer']['date']=='2023-10-01T18:22:35Z','October repository date');ok(len(j['files'])==300,'API listing partial qualification')
license=(A/'collector_LICENSE.txt').read_text();ok('MIT License' in license and 'Copyright (c) 2022 Brian Lee Cheow Teng' in license and 'notice shall be included' in license,'actual MIT notice')
for row in rb['local_sources']:
 b=Path(row['path']).read_bytes();ok(sha(b)==row['sha256'] and len(b)==row['size'],'paper/audit pin '+Path(row['path']).name)
paper=Path(rb['local_sources'][2]['path']).read_text();ok('65 entities' in paper and '25 are identified as associated with Alameda Research' in paper,'paper65entities25');ok(not any(x.casefold() in paper.casefold() for x in ('Coquidé','Cazabet','Tovanich','2409.10949','brianleect')),'no comparison/collector reference in retained text')
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,d):self.parts.append(d)
extract={}
for name in ['comparison_primary.html','comparison_successor.html']:
 p=Text();p.feed((A/name).read_text());s=' '.join(' '.join(p.parts).split());extract[name]=s
 (H/(name+'.txt')).write_text(s+'\n')
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'raw_source_pins':{r['path']:r['sha256'] for r in m if r['type']=='file'},'external_refetch':False},indent=2)+'\n');print(len(checks))
