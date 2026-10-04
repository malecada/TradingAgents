import pathlib,json,hashlib,re,datetime
D=pathlib.Path(__file__).resolve().parent
R=D.parents[3]; S=D.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
checks=[]
for p in sorted(D.glob('*.receipt.json')):
 m=json.loads(p.read_text())
 if 'sha256' in m:
  b=(D/p.name.removesuffix('.receipt.json')).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'];checks.append({'receipt':p.name,'verified':True})
t=json.loads((D/'collector_tree.json').read_text());assert t['truncated'] is False
tree={v['path']:v for v in t['tree']}
joins=[]
for path,name in [('data/etherscan/accounts/fund.json','historical_fund.json'),('data/etherscan/accounts/alameda-research.json','historical_alameda.json'),('README.md','collector_README.md'),('LICENSE','collector_LICENSE.txt')]:
 b=(D/name).read_bytes();v=tree[path];oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert v['type']=='blob' and v['mode']=='100644' and v['sha']==oid and v['size']==len(b);joins.append(dict(path=path,local=name,git_blob_oid=oid,sha256=sha(b),size=len(b),git_mode=v['mode']))
c=json.loads((D/'collector_commit.json').read_text())[0];assert c['sha']=='923aba72c7e2d0682f7ae6194b6140bd90668dc9'
j=json.loads((D/'fund_june_commit.json').read_text());fj=next(v for v in j['files'] if v['filename']=='data/etherscan/accounts/fund.json');assert fj['sha']==joins[0]['git_blob_oid']
f=json.loads((D/'historical_fund.json').read_text());old=json.loads((D/'historical_fund_march.json').read_text());assert len(f)==65 and len(old)==64
assert all(re.fullmatch('0x[0-9a-f]{40}',a) and type(v)is str for a,v in f.items())
numbered={k:v for k,v in f.items() if re.fullmatch('Alameda Research [0-9]+',v)}
associated={k:v for k,v in f.items() if v.startswith('Alameda Research')}
assert len(numbered)==25 and len(associated)==27
ordered=sorted(f);body=('\n'.join(ordered)+'\n').encode();(D/'ORDERED_ADDRESSES01.txt').write_bytes(body)
records=[{'address':a,'label':f[a]} for a in ordered]
canonical=(json.dumps(records,sort_keys=True,separators=(',',':'))+'\n').encode();(D/'ORDERED_MEMBERSHIP01.json').write_bytes(canonical)
local=[]
for rel in ['SOURCE_AUDIT.md','TABLE_COVERAGE.md','sources/paper.txt','sources/paper.pdf']:
 p=S/rel;b=p.read_bytes();local.append(dict(path=str(p),size=len(b),sha256=sha(b)))
text=(S/'sources/paper.txt').read_text();assert all(x not in text for x in ['Coquidé','Cazabet','Tovanich','2409.10949'])
readback={'schema_version':1,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'PARTIAL_HISTORICAL_COHORT_EVIDENCE_ONLY','cohort_status':'blocked_cohort','author_reuse_authenticated':False,'collector_commit':c['sha'],'collector_commit_date':c['commit']['committer']['date'],'fund_file_last_commit':j['sha'],'fund_file_commit_date':j['commit']['committer']['date'],'collector_is_original_scrape_artifact_not_etherscan_attestation':True,'file_specific_api_page_files':len(j['files']),'api_whole_commit_filelist_claim':False,'joins':joins,'receipt_checks':checks,'local_sources':local,'candidate_count':65,'numbered_alameda_count':25,'all_alameda_named_count':27,'numbered_alameda_suffixes':sorted(int(v.rsplit(' ',1)[1])for v in numbered.values()),'deposit_accounts':{k:v for k,v in associated.items() if k not in numbered},'march_count':64,'added_since_march':{k:f[k]for k in sorted(f.keys()-old.keys())},'removed_since_march':sorted(old.keys()-f.keys()),'changed_labels_since_march':{k:[old[k],f[k]]for k in sorted(old.keys()&f.keys())if old[k]!=f[k]},'address_membership_encoding':'lowercase sorted address strings, one per LF line, final LF; ASCII','address_membership_sha256':sha(body),'address_label_membership_encoding':'sorted-address array of address,label objects; JSON sorted keys compact separators plus final LF; UTF-8','address_label_membership_sha256':sha(canonical),'empirical_admission':False,'original_tables_replication_ready':False,'prospective_assumption_requires_separate_frozen_registration':True}
save('READBACK01.json',readback);print(json.dumps({k:readback[k]for k in ['candidate_count','address_membership_sha256','address_label_membership_sha256','added_since_march','decision']}))
