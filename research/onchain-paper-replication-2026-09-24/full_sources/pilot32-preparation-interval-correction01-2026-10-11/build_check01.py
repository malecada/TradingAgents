import ast,copy,difflib,hashlib,json,types
from pathlib import Path
R=Path.cwd();P=Path(__file__).resolve().parent;S=R/'tradingagents/research/onchain_replication/compact_mcm.py';old=S.read_text()
start=old.index('    matching = thaw(owner.matching); ordered =',old.index('def _prepare('));end=old.index('    run = owner.bound._run;',start)
block=old[start:end];legacy=block[:block.index('    if _imported(dictionary):')]
replacement="    if imported:\n        expected=dictionary.derive_scope();require(expected==dictionary.scope,'imported producer scope differs')\n    else:\n"+''.join('    '+line if line.strip() else line for line in legacy.splitlines(True))
new=old[:start]+replacement+old[end:];assert new.replace(replacement,block,1)==old
(P/'compact_mcm.py').write_text(new)
for name,a,b,pa,pb in [('forward.patch',old,new,str(S.relative_to(R)),str((P/'compact_mcm.py').relative_to(R))),('inverse.patch',new,old,str((P/'compact_mcm.py').relative_to(R)),str(S.relative_to(R)))]:
 (P/name).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=pa,tofile=pb)))
assert ast.dump(ast.parse(new.replace(replacement,block,1)),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
checks=[]
def ck(v,n):assert v,n;checks.append(n)
def require(ok,msg):
 if not ok:raise ValueError(msg)
def run(text,imported,mutate=False):
 events=[];d=types.SimpleNamespace(representatives=['m0','m1'],identity='dict',matching_config_hash='matching')
 scope={'graph':'g','node_order':'authenticated-order','dictionary':'dict','ordered_motifs':'m','matching':'matching','workflow':'imported'}
 dictionary=types.SimpleNamespace(scope=dict(scope),derive_scope=lambda:(events.append('derive_scope') or ({**scope,'graph':'changed'} if mutate else dict(scope))))
 owner=types.SimpleNamespace(matching={'x':1},bound=types.SimpleNamespace(record={'workflow_identity':'workflow'}));graph=types.SimpleNamespace(node_ids=['a','b','c'])
 def order(ids):events.append('legacy_node_order_traversal');return 'node-order'
 def identity(g):events.append('motif_identity');return g
 ns={'imported':imported,'dictionary':dictionary,'owner':owner,'graph':graph,'d':d,'key':'g','BACKEND':'backend','thaw':copy.deepcopy,'graph_identity':identity,'node_order_hash':order,'cache_key':lambda v:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),'require':require,'_imported':lambda _:imported}
 try:exec(compile('if True:\n'+text,'synthetic-scope-block','exec'),ns);return ns['expected'],events,None
 except ValueError as e:return None,events,str(e)
a,ea,_=run(block,True);b,eb,_=run(replacement,True)
ck(a==b,'imported exact expected value retained');ck(ea.count('legacy_node_order_traversal')==1 and eb.count('legacy_node_order_traversal')==0,'RED old discarded full order scan GREEN absent')
ck(eb==['derive_scope'],'only genuine imported derivation')
a,ea,e=run(block,False);b,eb,f=run(replacement,False);ck((a,ea,e)==(b,eb,f),'legacy result and hook order unchanged')
ck(run(block,True,True)[2]==run(replacement,True,True)[2]=='imported producer scope differs','fresh imported scope mutation same refusal')
# Verify entire enclosing function outside the exact local branch replacement is unchanged.
ck(new[:start]==old[:start] and new[start+len(replacement):]==old[end:],'all callbacks guards final joins unchanged outside scope construction')
ck(new.count('dictionary.check()')==old.count('dictionary.check()'),'all dictionary checks retained')
# Original interval on an explicitly hypothetical clock isolates observed margin arithmetic only.
interval_source=(R/'tradingagents/research/onchain_replication/imported_authority_interval.py').read_text();ns={};exec(compile(interval_source,'original-interval','exec'),ns)
policy={'schema_version':1,'kind':ns['KIND'],'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':30000,'max_stale_ms':60000,'max_calls_between_full':100000,'assumption':ns['ASSUMPTION']}
def timed(age,cost):
 t=[age];i=ns['Interval'](policy,clock=lambda:t[0]);i.full=i.live=i.finger=0
 def full():t[0]+=cost
 try:i.validate(full,lambda:None,lambda:None,boundary=True);return 'pass'
 except ValueError as e:return str(e)
ck('stale interval cannot refresh' in timed(49.924078479001764,10.453950685994641),'observed timing RED reproduced')
ck(timed(49.924078479001764-0.5,10.453950685994641)=='pass','conditional GREEN if discarded work saves0.5s; not measured')
ck('stale interval cannot refresh' in timed(49.924078479001764-0.1,10.453950685994641),'insufficient savings still fails60s')
result={'classification':'SYNTHETIC_SOURCE_CONTROL_FLOW_AND_CONDITIONAL_CLOCK_ONLY','checks':checks,'source_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest(),'observed_age_seconds':49.924078479001764,'observed_full_callback_seconds':10.453950685994641,'observed_total_seconds':60.378029164996406,'minimum_unchanged_callback_savings_to_reach60_seconds':0.378029164996406,'actual_removed_traversal_elapsed_seconds':None,'real_success_claim':False,'production_imports':False}
(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
