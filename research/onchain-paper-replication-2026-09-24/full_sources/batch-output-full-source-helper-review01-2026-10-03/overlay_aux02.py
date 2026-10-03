import ast,copy,hashlib,json,runpy,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'batch-output-full-source-helper-preparation01-2026-10-03';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];members=[]
def ck(x,label):
 assert x,label
 checks.append(label)
v=json.loads((P/'SOURCE_INVENTORY01.json').read_bytes());actual={x['target']:x['sha256'] for x in v['entries']}
cap=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');initial=json.loads((P/'ORIGIN_ROWS_INITIAL01.json').read_bytes());reg=json.loads((cap/'held-fixture-registration01.json').read_bytes());expected={n:h for n,h in reg['experiments']['original-import-held-success-20261003-01']['source_files'].items() if n not in initial['baseline_auxiliary_paths']}
for name in ('held-consumer-selected-transfer-worker-preparation02-2026-10-03','batch-output-produced-f32-adapter-preparation02-2026-10-03'):
 d=O.parent/name;m=json.loads((d/'MANIFEST02.json').read_bytes())
 for r in m['members']:
  p=d/r['path'];s=p.lstat();raw=p.read_bytes();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(raw)==r['bytes'] and sha(raw)==r['sha256'],'frozen origin '+name+'/'+r['path']);members.append({'path':str(p),'mode':oct(stat.S_IMODE(s.st_mode)),'type':'regular',**{k:r[k] for k in ('sha256','bytes')}})
 for r in json.loads((d/'INSTALL_MAP02.json').read_bytes())['changes']:expected[r['target']]=r['sha256']
for r in json.loads((P/'INSTALL_MAP01.json').read_bytes())['changes']:expected[r['target']]=r['sha256']
ck(expected==actual,'exact actual199 then worker02 then raw02 then three helpers overlay')
# Test dictionaries only, no Owner/Binding/Run or native capability. Reuse labelled
# author fixture builder, independently attack boundaries and retain exceptions.
f=runpy.run_path(str(P/'test_auxiliary03.py'));G=f['G'];failed=[]
for label,mutation in [
 ('missing allocation',lambda s,r:r.pop('budget_allocation')),
 ('extra207 member',lambda s,r:r['registration']['document']['experiments']['future-held-fixture']['source_files'].update({'extra':'a'*64})),
 ('extra208 package',lambda s,r:s['package_files'].update({'extra':'a'*64})),
 ('replace helper source pin',lambda s,r:r['registration']['document']['experiments']['future-held-fixture']['source_files'].update({next(iter(s['source_files'])):'f'*64})),
 ('self-registration source cycle',lambda s,r:r['auxiliary_sources']['reference'].update(path=r['registration']['reference']['path'])),
 ('extra role',lambda s,r:r.update(unknown=None)),
 ('null review',lambda s,r:r.update(budget_review=None)),
 ('alias charter implementation',lambda s,r:r['charter']['reference'].update(path=next(iter(s['source_files'])))),
 ('declaration wrong count',lambda s,r:r['auxiliary_sources']['document'].update(implementation_source_count=199)),
 ('declaration wrong map hash',lambda s,r:r['auxiliary_sources']['document'].update(implementation_map_sha256='e'*64)),
]:
 s,r=f['fixture']();mutation(s,r)
 try:G['full_held_input_plan'](r,s)
 except (ValueError,KeyError,TypeError) as e:failed.append({'case':label,'exception':type(e).__name__,'message':str(e)})
 else:raise AssertionError('accepted '+label)
s,r=f['fixture']();out=G['full_held_input_plan'](r,s);ck(out['auxiliary_metadata']['admission_source_count']==207 and not out['execution_admitted'],'qualified positive207 remains unregistered')
ck(not any(n.split('.')[0] in ('numpy','torch','scipy') for n in sys.modules),'stdlib only')
(O/'OVERLAY_AUX02.json').write_text(json.dumps({'checks':checks,'refusals':failed,'origin_members':members,'qualification':'labelled unregistered metadata fixtures only, no genuine future source or authority'},indent=2)+'\n')
print('PASS',len(checks),'overlay/origin/auxiliary checks;',len(failed),'independent aux refusals')
