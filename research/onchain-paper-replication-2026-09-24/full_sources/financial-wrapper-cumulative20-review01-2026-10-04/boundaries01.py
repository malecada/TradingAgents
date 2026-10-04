import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hist=S/'fixture_inputs/financial_wrapper_registration01/review-cumulative/HISTORY_READBACK01.json';assert sha(hist)=='d49124a2c812abc1be5cc9646d4b3d11c9904a411fcfd01f9d323f114a019df1';v=json.loads(hist.read_text());paper=v['paper'];rows=[]
for row in paper['claims']:
 c=Path(row['claim_path']);t=Path(row['terminal_path'])
 assert c.resolve()==c and t.resolve()==t and c.stat().st_size<=4194304 and t.stat().st_size<=4194304
 assert sha(c)==row['claim_sha256'] and sha(t)==row['terminal_sha256']
 cv=json.loads(c.read_bytes());tv=json.loads(t.read_bytes());assert tv['experiment_id']==cv['experiment_id']==row['identity'] and tv['status']==row['status'] and tv['claim_sha256']==row['claim_sha256']
 assert cv['family']['mechanism_id']!='synthetic-full-financial-wrapper-v1'
 rows.append({'identity':row['identity'],'status':row['status'],'claim_sha256':row['claim_sha256'],'terminal_sha256':row['terminal_sha256'],'program_id':cv['program_id'],'allowance':cv.get('effective_attempt_budget',cv['family']['attempt_budget'])})
assert len(rows)==36 and sum(r['status']=='complete' for r in rows)==27 and sum(r['status']=='failed' for r in rows)==9
current=[r for r in rows if r['program_id']=='onchain-paper-replication-2026-09-24'];assert len(current)==19 and max(r['allowance'] for r in current)==64
(H/'PAPER_BOUNDARY01.json').write_text(json.dumps({'scope':'exact36 recorded historical+current paper claims/terminals rehashed, not a universal search for unknown roots','historical_review_sha256':sha(hist),'closed':36,'complete':27,'failed':9,'current':19,'prior':17,'highest_current':64,'draft20_mechanism_distinct':True,'rows':rows},indent=2)+'\n')
# Guard03 acceptance is authenticated as an exact independent source review, not re-executed.
p=B/'financial-wrapper-storage-watch-concurrent-publication-review03-2026-10-04';m=json.loads((p/'MANIFEST01.json').read_text());machine=json.loads((p/'MACHINE01.json').read_text());verified=0
for r in m['members']:
 q=p/r['path'];s=q.lstat()
 assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':assert s.st_size==r['bytes'] and sha(q)==r['sha256']
 elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 elif r['kind']=='symlink':assert os.readlink(q)==r['target']
 else:raise AssertionError('unknown kind')
 verified+=1
assert machine['decision']=='ACCEPTED_SOURCE_ONLY_STORAGE_WATCH_CORRECTION03' and machine['source_sha256']=='91e21c525a156cc8c25877ac35f0308896a1a0d1e6279d5aecf91d7e02567780' and machine['numerical_authority'] is False
(H/'GUARD_REVIEW_BINDING01.json').write_text(json.dumps({'manifest_sha256':sha(p/'MANIFEST01.json'),'machine_sha256':sha(p/'MACHINE01.json'),'verified_declared_members':verified,'review_source_sha256':machine['source_sha256'],'source_only':True,'native_or_source_adoption_authority':False},indent=2)+'\n')
print(json.dumps({'paper_closed':36,'paper_highest64_unchanged':True,'guard_review_members':verified}))
