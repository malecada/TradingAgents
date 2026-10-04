from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;F=D.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');checks=[]
def ok(v,n):assert v,n;checks.append(n)
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304 and p.resolve()==p,'safe regular read');b=p.read_bytes();ok(p.lstat()==s,'sampled unchanged');return b
def J(p):return json.loads(read(p))
q=J(D/'READBACK01.json');base=J(F/'financial-wrapper-compatibility-root-integration01-2026-10-04/SOURCE_ADOPTION_AFTER589.json');rows={x['path']:x for x in base['members']};protected=J(F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04/PROTECTED_NON_TARGET585.json');ok(len(protected['members'])==585,'585protected')
for x in protected['members']:ok(rows[x['path']]==x,'protected original row exact')
cp=[]
for p,x in q['checked_files'].items():
 if '/checkpoints/' not in p or not p.endswith('/manifest.json'):continue
 p=Path(p);m=J(p);ok(h(read(p))==x['sha256'],'actual checkpoint original manifest')
 for n,member in m['members'].items():
  b=read(p.parent/n);ok(len(b)==member['size'] and h(b)==member['sha256'],'opaque original checkpoint member')
 cp.append({'path':str(p),'sha256':x['sha256'],'source_commit':m['provenance']['source_commit'],'source_hashes':m['provenance']['source_hashes'],'members':m['members']})
old100=[x for x in cp if '/financial-wrapper-classification-eager-complete100-20261003-01/' in x['path']];one=[x for x in cp if '/financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01/' in x['path']];ok(len(old100)==29 and len(one)==1,'29 failed100 plus1 interrupted checkpoints');ok(all(x['source_commit']=='9dc5c79f738920b52947b4e63fed0397f1b5b207' for x in old100),'old100 provenance retained');ok(one[0]['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816' and len(one[0]['source_hashes'])==194,'original interrupted historical194 provenance')
claims=[J(CAP/'research_runs'/x['identity']/'claim.json') for x in q['actual_claims']];ok(sorted(x['effective_attempt_budget'] for x in claims)==[18,19,19],'actual18/19/19 allowances');ok({x['experiment']['family'] for x in claims}=={'synthetic-financial-wrapper'},'same original family')
newfiles=q['new_file_pins'];rows15={n:{'sha256':pin,'mode':0o600,'kind':'file'} for n,pin in newfiles.items()}
def valid(candidate):return set(candidate)==set(rows15) and all(candidate[n]==rows15[n] for n in rows15)
ok(valid(rows15),'exact15 scope positive');controls=[]
for n in rows15:
 bad={k:dict(v) for k,v in rows15.items()};del bad[n];ok(not valid(bad),'missingpath refusal');controls.append('missing '+n)
 bad={k:dict(v) for k,v in rows15.items()};bad[n]['sha256']='0'*64;ok(not valid(bad),'changedbody refusal');controls.append('hash '+n)
 bad={k:dict(v) for k,v in rows15.items()};bad[n]['mode']=0o644;ok(not valid(bad),'changedmode refusal');controls.append('mode '+n)
 bad={k:dict(v) for k,v in rows15.items()};bad[n]['kind']='symlink';ok(not valid(bad),'changedtype refusal');controls.append('type '+n)
bad={**rows15,'research_runs/old/claim.json':{'sha256':'0'*64,'mode':0o600,'kind':'file'}};ok(not valid(bad),'broad historical staging refusal');controls.append('extra old claim')
(D/'SUPPLEMENT01.json').write_text(json.dumps({'checks':len(checks),'checkpoint_manifests':cp,'opaque_member_decode':False,'old100_durable_checkpoints':29,'old100_complete_credit':False,'interrupted194_hashes_retained':True,'protected585':True,'scope_refusal_controls':controls,'controls_are_metadata_only':True},indent=2)+'\n');print(len(checks),len(cp),len(controls))
