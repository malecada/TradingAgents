from pathlib import Path
import shutil
P=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/pilot40-continuation-contract-template-candidate-2026-10-12')
I=P/'iteration01';I.mkdir()
for x in list(P.iterdir()):
 if x.is_file():shutil.copy2(x,I/x.name)
p=P/'batched_continuation.py';s=p.read_text()
s=s.replace('    from . import compact_mcm_batched\n','    from . import compact_mcm_batched, job\n    from .provenance import thaw\n',1)
s=s.replace("and template['workflow_identity'] is None and template['descriptor_sha256'] is None,\n        'exact two-slot", "and template['workflow_identity'] is None and template['descriptor_sha256'] is None\n        and template['source_sha256'] is None,\n        'exact three-slot")
needle="    policy=_json(raw)\n    _poll_target(run,target)"
repl="""    policy=_json(raw)
    pair_role=m['runtime_pair_policy_input']
    require(type(pair_role) is str and pair_role in run.admission.inputs and pair_role!=role,
        'distinct registered runtime pair policy required')
    pair_raw=_bounded_input(run,pair_role,max_bytes=2*1024**2,target=target)
    pair=_json(pair_raw);numerical=m['numerical_source']
    require(type(numerical) is dict and set(numerical)=={'commit','files'}
        and type(numerical['commit']) is str and len(numerical['commit'])==40
        and all(c in '0123456789abcdef' for c in numerical['commit'])
        and type(numerical['files']) is dict and set(numerical['files'])==job.required_sources(),
        'exact numerical source closure required')
    require(type(pair) is dict and set(pair)=={'schema_version','backend','limits','numerical_source'}
        and type(pair['schema_version']) is int and pair['schema_version']==1
        and digest(pair_raw)==target.owner.bound.record['policy_sha256']
        and body(pair['numerical_source'])==body(numerical)
        and body(thaw(target.owner.bound.record['numerical_source']))==body(numerical),
        'registered pair policy and bound numerical source differ')
    require(all(type(value) is str and len(value)==64
        and all(c in '0123456789abcdef' for c in value)
        and run.admission.experiment['source_files'].get(name)==value
        for name,value in numerical['files'].items()),'admitted numerical source closure differs')
    _poll_target(run,target)"""
assert needle in s;s=s.replace(needle,repl,1)
s=s.replace("frozen={**current,'workflow_identity':None,'descriptor_sha256':None}","frozen={**current,'source_sha256':None,'workflow_identity':None,'descriptor_sha256':None}")
s=s.replace("and review['runtime_policy_input']==m['runtime_policy_input'], 'reviewed contract template differs')","and review['runtime_policy_input']==m['runtime_policy_input']\n            and review['runtime_pair_policy_input']==m['runtime_pair_policy_input']\n            and review['numerical_source_sha256']==digest(body(m['numerical_source'])),\n            'reviewed contract template differs')")
p.write_text(s)
p=P/'check01.py';s=p.read_text()
s=s.replace("ad=N(experiment={'source_files':{'source.py':'5'*64}},inputs={'mcm':{'path':'mcm.json','sha256':digest(body(self.policy))}})","self.numerical={'commit':'a'*40,'files':{f'source{i}.py':'5'*64 for i in range(206)}}\n  self.pair={'schema_version':1,'backend':'fixture','limits':{},'numerical_source':copy.deepcopy(self.numerical)}\n  ad=N(experiment={'source_files':{**self.numerical['files'],'metadata.json':gate_hash}},inputs={'mcm':{'path':'mcm.json','sha256':digest(body(self.policy))},'pair':{'path':'pair.json','sha256':digest(body(self.pair))}})")
s=s.replace("'workflow_identity':'6'*64}","'workflow_identity':'6'*64,'policy_sha256':digest(body(self.pair)),'numerical_source':copy.deepcopy(self.numerical)}")
s=s.replace("template={**c,'workflow_identity':None,'descriptor_sha256':None}","template={**c,'source_sha256':None,'workflow_identity':None,'descriptor_sha256':None}")
s=s.replace("'runtime_policy_input':'mcm'}","'runtime_policy_input':'mcm','runtime_pair_policy_input':'pair','numerical_source':copy.deepcopy(t.numerical)}")
s=s.replace("events.append('read');return body(t.policy)","events.append('read');return body(t.policy if role=='mcm' else t.pair)")
s=s.replace("env=dict(require=require,", "env=dict(job=N(required_sources=lambda:set(t.numerical['files'])),thaw=copy.deepcopy,require=require,")
s=s.replace("['read','poll','validate']","['read','read','poll','validate']")
s=s.replace('test_only_two_null_slots','test_only_three_null_slots').replace("('source_sha256','config_sha256'","('config_sha256'")
s=s.replace("for field in ('workflow_identity','descriptor_sha256'):","for field in ('source_sha256','workflow_identity','descriptor_sha256'):")
s=s.replace("'two-slot'","'three-slot'")
s=s.replace("if __name__=='__main__':",'''class Amendment(Checks):
 def test_source_map_cycle_and_closure(self):
  a=fixture('a','7'*64);b=fixture('b','8'*64)
  self.assertEqual(body(a[3]['contract']),body(b[3]['contract']))
  self.assertNotEqual(a[1]['source_sha256'],b[1]['source_sha256'])
  for t,c,d,m,e,_ in (a,b):self.assertEqual(e['_bind_contract_template'](t.owner.bound._run,t,m,c),d)
  for change in ('commit','missing','extra','pin','binding','pair','role','admitted'):
   t,c,d,m,e,_=fixture()
   if change=='commit':m['numerical_source']['commit']='b'*40
   if change=='missing':del m['numerical_source']['files']['source0.py']
   if change=='extra':m['numerical_source']['files']['extra.py']='5'*64
   if change=='pin':m['numerical_source']['files']['source0.py']='6'*64
   if change=='binding':t.owner.bound.record['numerical_source']['commit']='b'*40
   if change=='pair':t.pair['limits']={'changed':True}
   if change=='role':m['runtime_pair_policy_input']='mcm'
   if change=='admitted':t.owner.bound._run.admission.experiment['source_files']['source0.py']='6'*64
   with self.subTest(change=change),self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
if __name__=='__main__':''')
p.write_text(s)
