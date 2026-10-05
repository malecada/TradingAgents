"""Focused source/null/refusal and actual local opaque archive checks; no entry."""
import ast,copy,hashlib,json,os
from pathlib import Path
import outcome01 as O
R=O.R;H=O.HERE;checks=[]
def ok(n,v):
 assert v,n
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,AssertionError,TypeError):checks.append(n)
 else:raise AssertionError(n)
q=json.loads(R.read(H,'REQUEST_DRAFT01.json'));raw=R.read(H,'CAPTURE01.json');c=O.context(raw)
refuse('null actual commit refuses generation',lambda:O.generate(q,raw))
refuse('changed capture refuses',lambda:O.context(raw+b' '))
refuse('another lane refuses',lambda:O.lane_root(1,'remote'))
refuse('unsafe phase refuses',lambda:O.lane_root(0,'../flat'))
q['commit']='487583875a103290ead73aef21f75e3e28880512' # genuine historical Main syntax only, not final eligible binding
g=O.generate(q,raw);ok('canonical receiver encoding',g['selection_body']==O.selection_encode({'remote_commit':q['commit'],'rows':[dict(path=n,**v) for n,v in sorted(q['required'].items())]}))
for n,s in [('receiver',g['receiver']),('receipt',g['receipt']),*g['callers'].items()]:ast.parse(s);checks.append('generated AST '+n)
ok('exact fresh namespace',"fresh-continuation-current01.git" in g['receiver'])
for role in ('remote','flat'):ok('exact caller namespace '+role,str(O.lane_root(0,role).name) in g['callers'][role])
for mode in ('missing','extra','changed'):
 v=copy.deepcopy(q);key=next(iter(v['required']))
 if mode=='missing':del v['required'][key]
 elif mode=='extra':v['required']['../outside']={'bytes':0,'sha256':'0'*64}
 else:v['required'][key]['sha256']='0'*64
 refuse('selection '+mode,lambda:O.selected_required(v,0,c))
v=copy.deepcopy(q);v['release']={'name':'../outside','sha256':'0'*64};refuse('release traversal',lambda:O.request_core_sha256(v))
v=copy.deepcopy(q);v['proofs']['future_full_current_recovery']={};refuse('invented future recovery',lambda:O.selected_required(v,0,c))
original=(H/'recover.template01.py').read_text();inverse=g['receiver']
for a,b in reversed(g['receiver_changes']):assert inverse.count(b)>=1;inverse=inverse.replace(b,a)
ok('full literal receiver inverse',inverse==original);ok('full AST receiver inverse',ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False))
m=json.loads(R.read(H,'archive-manifest.json'));R.validate(m);ok('full actual175/159',len(m['members'])==175 and sum(r['kind']=='file' for r in m['members'])==159)
out=H/'local-opaque-roundtrip';out.mkdir(mode=0o700);result=R.restore(H/'increment.tar.gz',c['archive_pin'],m,out)
meta=json.loads(R.read(out,result['metadata_file']));ok('restored whole original manifest',meta['manifest']==m)
for r in m['members']:
 if r['kind']=='file':b=R.read(out,meta['flat_members'][r['path']]);assert len(b)==r['bytes'] and R.digest(b)==r['sha256']
checks.append('all159 actual local flat bodies')
sink=R.Sink();R.tar_stream(H/'snapshot',m,sink);ok('canonical full re-encoding',sink.count==c['archive_pin']['bytes'] and sink.hash.hexdigest()==c['archive_pin']['sha256'])
ok('Root destinations still absent',all(not os.path.lexists(O.lane_root(0,p)) for p in ('remote','flat')))
print(json.dumps({'passed':len(checks),'checks':checks,'selected_bodies':len(q['required']),'selected_bytes':sum(v['bytes'] for v in q['required'].values()),'local_roundtrip':result,'actual_remote_or_Root_entry_executed':False,'historical_commit_used_for_syntax_only':q['commit']},sort_keys=True))
