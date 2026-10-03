"""Actual cleanup reducer/handler and retained original metadata, stdlib only."""
import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));os.environ['MCM_SOURCE']=str(D/'compact_mcm.py')
from test_cleanup03 import handler
p=D.parent/'original-import-fixture-io-candidate02-2026-10-02/owned_io.py'
s=importlib.util.spec_from_file_location('review_owned_io',p);io=importlib.util.module_from_spec(s);s.loader.exec_module(io)
for variant in ('ordinary','first-fatal','later-fatal','uncertain'):
 owner=types.SimpleNamespace(poisoned=False,identity='a'*64);calls=[]
 primary=MemoryError('first actual fatal') if variant=='first-fatal' else ValueError('primary')
 later=KeyboardInterrupt('later actual fatal') if variant=='later-fatal' else OSError('uncertain close')
 def stream_close():
  calls.append('stream')
  if variant in ('first-fatal','later-fatal','uncertain'):raise later
 def log_fail(message):
  assert not owner.poisoned;calls.append('log-failed-terminal')
 def log_close():calls.append('log-close')
 def marker(*a):calls.append('producer-failed-marker')
 env={'owner':owner,'stream':types.SimpleNamespace(closed=False,close=stream_close),'log':types.SimpleNamespace(closed=False,fail=log_fail,close=log_close),'claimed':True,'fd':1,'sentinel':primary,'io':types.SimpleNamespace(_cleanup=io._cleanup,_json=lambda x:x,_write=marker)}
 exec(handler(),env)
 try:env['selected']();raise AssertionError('handler unexpectedly returned')
 except BaseException as actual:
  assert owner.poisoned and calls==['stream','log-failed-terminal','log-close','producer-failed-marker']
  if variant in ('ordinary','first-fatal'):assert actual is primary
  elif variant=='later-fatal':assert actual is later
  else:assert type(actual) is io.CleanupFailure and primary in actual.failures and later in actual.failures
 print('Actual cleanup reducer and handler:',variant,'PASS')
# Pure semantic authentication of all eleven preserved actual original JSON bodies.
from original_semantics import expected_numeric
root=D.parent/'original-import-native-release-2026-10-03/capsule01'
gate=json.loads((root/'fixture-registration.json').read_bytes());exp=gate['experiments']['original-import-native-success-20261003-01'];inputs=exp['inputs']
load=lambda name:json.loads((root/inputs[name]['path']).read_bytes())
job=load('execution_job');selection=next(iter(job['payload']['representation_jobs'].values()));policy=load(selection['original_dictionary_input']);blobs={}
for role,reference in policy['refs'].items():
 info=inputs[reference['input']];raw=(root/info['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==info['sha256']==reference['sha256'];blobs[role]=raw
result=expected_numeric(policy,blobs)
assert result['original_dictionary']=='48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726'
print('All',len(blobs),'actual retained original JSON bodies semantically authenticated; ordered motifs',len(result['ordered_motifs']),'numeric byte extent',result['numeric_bytes'])
assert not any(k.split('.')[0] in ('numpy','torch','scipy','tradingagents') for k in sys.modules)
print('No numerical/package imports or authority claims.')
