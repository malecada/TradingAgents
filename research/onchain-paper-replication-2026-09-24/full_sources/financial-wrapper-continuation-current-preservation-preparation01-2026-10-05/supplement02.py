"""Add genuine new draft/proof bytes; reuse the already completed opaque CAP census."""
import json,os,stat,time
from pathlib import Path
import bind02 as B
H=Path(__file__).resolve().parent
def put(name,raw):
 with B.IO._opened(H/name,'xb') as s:s.write(raw);s.flush();os.fsync(s.fileno())
def main():
 priorraw=B.IO._read_path(H/'CURRENT_COMPOSITION01.json',4*1024**2);prior=json.loads(priorraw)
 selected=json.loads(B.IO._read_path(H/'SELECTED_BODIES01.json',4*1024**2))
 c=B.Census();parent=c.tree(B.PARENT,{n:'file' for n in B.PARENT_NAMES},B.PARENT_NAMES);q=B.source_bound(c)
 oldparent={r['path']:r for r in prior['parent']['members']};newparent={r['path']:r for r in parent['members']}
 B.require(all(newparent[n]==r for n,r in oldparent.items()) and set(newparent)-set(oldparent)=={'REQUEST_SOURCE_BOUND_DRAFT01.json'},'exact one new Parent member')
 # Metadata-only fresh whole namespace observation; the opaque body hashes are
 # explicitly reused from the earlier complete measurement, never called reread.
 expected={r['path']:r for r in prior['capsule']['members']};seen={};signatures={}
 def visit(root,rel=''):
  c.tick();before=root.lstat();it=os.scandir(root)
  try:entries=sorted(it,key=lambda e:e.name)
  finally:B.IO._cleanup((it.close,))
  for e in entries:
   n=f'{rel}/{e.name}'.lstrip('/')
   if n=='.git':continue
   B.require(n in expected,'new unlisted CAP member');p=B.CAP/n;s=p.lstat();r=expected[n]
   B.require(stat.S_IMODE(s.st_mode)==r['mode'],'CAP original mode')
   if r['kind']=='directory':B.require(stat.S_ISDIR(s.st_mode),'CAP directory');visit(p,n)
   else:B.require(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'],'CAP regular extent')
   signatures[str(p)]=B.sig(s);seen[n]=True
  B.require(B.sig(root.lstat())==B.sig(before),'CAP directory churn');signatures[str(root)]=B.sig(before);c.tick()
 visit(B.CAP);B.require(set(seen)==set(expected),'complete CAP metadata membership')
 B.require(B.git(B.CAP,['rev-parse','HEAD'],cap=128).decode().strip()==B.SOURCE,'current source unchanged')
 for r in selected['bodies']:
  raw=B.IO._read_path(H/r['path'],4*1024**2);B.require(len(raw)==r['bytes'] and B.sha(raw)==r['sha256'],'retained original selected body')
 additions=[(str(B.PARENT),'REQUEST_SOURCE_BOUND_DRAFT01.json')]+[(str(B.PROOFDIR),n) for n in sorted(B.PROOFS)]
 for root,name in additions:
  raw=c.saved[(root,name)];role='parent' if root==str(B.PARENT) else 'source-proof';local=f"new-bytes/{len(selected['bodies']):03d}-{role}.body";put(local,raw)
  selected['bodies'].append({'role':role,'original_root':root,'original_path':name,'original_mode':stat.S_IMODE((Path(root)/name).lstat().st_mode),'path':local,'bytes':len(raw),'sha256':B.sha(raw),'stored_mode':0o600})
 c.finish()
 for p,s in signatures.items():c.tick();B.require(B.sig(Path(p).lstat())==s,'late CAP metadata change')
 prior.update(parent=parent,source_bound_request={'path':str(B.PARENT/'REQUEST_SOURCE_BOUND_DRAFT01.json'),'sha256':B.sha(c.saved[(str(B.PARENT),'REQUEST_SOURCE_BOUND_DRAFT01.json')])},proofs=q['proofs'],initial_measurement={'path':str(H/'CURRENT_COMPOSITION01.json'),'sha256':B.sha(priorraw),'all818_body_hashes_reused':True},supplement={'parent_and_proof_bytes_freshly_read':c.read_bytes,'CAP_metadata_only_rejoined':True,'whole_CAP_hashes_reread':False,'elapsed_seconds':time.monotonic()-c.start},future={'final_request':None,'source_runtime_proof':q['proofs']['independent_source_input_runtime'],'cumulative_proof':q['proofs']['cumulative'],'whole_current_recovery':None,'final_release':None})
 selected.update(count=len(selected['bodies']),bytes=sum(r['bytes'] for r in selected['bodies']),initial_selection={'path':str(H/'SELECTED_BODIES01.json'),'sha256':B.sha((H/'SELECTED_BODIES01.json').read_bytes())})
 put('CURRENT_COMPOSITION02.json',B.encode(prior));put('SELECTED_BODIES02.json',B.encode(selected))
 print(json.dumps({'selected_bodies':selected['count'],'selected_bytes':selected['bytes'],'CAP_files':823,'CAP_typed':1049,'Parent_files':len(parent['members']),'proof_files':2,'Git_old':407,'Git_current':416,'Git_new':9,'old_body_reread':False,'source':B.SOURCE,'full_recovery':None,'final_release':None},sort_keys=True))
if __name__=='__main__':main()
