"""Deterministic accepted-body overlay only. Never writes outside this directory."""
from pathlib import Path
import ast,difflib,hashlib,json,subprocess
D=Path(__file__).resolve().parent;ROOT=D.parents[3];F=D.parent;P=Path('tradingagents/research/onchain_replication');BASE='fc1e8f1e0e45ad122660a1d62a8c7e95c9d4519e'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_text())
N={k:'real-data-pilot-'+v for k,v in {
 'policy':'full-size-policy01-2026-10-05','population':'population-binding01-2026-10-05','composition':'model-entry-composition01-2026-10-05','checkpoint':'explicit-checkpoint-execution01-2026-10-05','throughput':'throughput-measurement01-2026-10-05','scope1':'writable-storage-scope01-2026-10-05','scope2':'writable-storage-scope02-2026-10-05','lease':'imported-authority-lease01-2026-10-06'}.items()}
def source(kind,name):return F/N[kind]/'candidate'/P/name
def inverse(text,edits):
 if not edits:return text
 if 'new_start' in edits[0]:
  lines=text.splitlines(True)
  for e in reversed(edits):
   assert lines[e['new_start']:e['new_end']]==e['new']
   lines[e['new_start']:e['new_end']]=e['old']
  return ''.join(lines)
 for e in reversed(edits):
  assert text.count(e['new'])==1
  text=text.replace(e['new'],e['old'])
 return text

def build():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
 selected={}
 for kind,names in [('policy',['resource_fixture.py']),('scope2',['resources.py','job.py','matching_owner.py','real_pilot_storage.py']),('checkpoint',['model.py','real_pilot_training.py']),('composition',['real_pilot_population.py']),('throughput',['real_pilot_throughput.py']),('lease',['imported_authority_interval.py','imported_authority_lease.py','imported_mcm_identity.py','mcm_score_stream.py','compact_mcm.py','real_pilot_import_caller.py'])]:
  for name in names:selected[name]=(kind,source(kind,name))
 evidence={};members={}
 for kind,name in N.items():
  directory=F/name;manifest=directory/('MANIFEST.json' if kind=='lease' else 'MANIFEST01.json');v=read(manifest)
  entries=v.get('members',v.get('files'))
  if type(entries) is list:entries={x['path']:x['sha256'] for x in entries}
  else:entries={k:(x if type(x) is str else x['sha256']) for k,x in entries.items()}
  evidence[kind]={'manifest':str(manifest.relative_to(ROOT)),'sha256':sha(manifest.read_bytes())};members[kind]=entries
 def evidence_read(kind,name):
  p=F/N[kind]/name;assert sha(p.read_bytes())==members[kind][name];return read(p)
 proofs=[]
 def prove(kind,name,baseline,edits):
  candidate=source(kind,name).read_text();actual=sha(candidate.encode());restored=inverse(candidate,edits)
  assert restored==baseline.read_text(),(kind,name)
  proofs.append({'kind':kind,'name':name,'candidate_sha256':actual,'baseline':str(baseline.relative_to(ROOT)),'baseline_sha256':sha(restored.encode()),'literal_inverse':True})
 for kind in ('policy','checkpoint'):
  for row in evidence_read(kind,'SOURCE_DELTA01.json')['files']:
   name=Path(row['path']).name;assert sha((ROOT/P/name).read_bytes())==row['baseline_sha256'];prove(kind,name,ROOT/P/name,row['edits'])
 comp=evidence_read('composition','COMPOSITION01.json')
 for row in comp['baselines']:prove('composition','real_pilot_import_caller.py',Path(row['origin']),row['edits'])
 row=evidence_read('throughput','SOURCE_DELTA01.json');prove('throughput','real_pilot_import_caller.py',Path(row['origin']),row['edits'])
 for name,row in evidence_read('scope1','SOURCE_DELTA01.json').items():prove('scope1',name,Path(row['baseline']),row['replacements'])
 for name,row in evidence_read('scope2','SOURCE_DELTA01.json').items():prove('scope2',name,source('scope1',name),row['edits'])
 for name,row in evidence_read('lease','SOURCE_DELTA01.json').items():prove('lease',name,Path(row['baseline']),row['edits'])
 result={};patch=[]
 for name,(kind,p) in sorted(selected.items()):
  raw=p.read_bytes();relative=str(p.relative_to(F/N[kind]));assert sha(raw)==members[kind][relative];ast.parse(raw)
  destination=D/'candidate'/P/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
  rel=str(P/name)
  try:old=subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT,stderr=subprocess.DEVNULL)
  except subprocess.CalledProcessError:old=None
  if old is not None:assert (ROOT/rel).read_bytes()==old
  else:assert not (ROOT/rel).exists()
  result[rel]={'source':str(p.relative_to(ROOT)),'source_manifest':evidence[kind],'sha256':sha(raw),'bytes':len(raw),'baseline_sha256':None if old is None else sha(old),'new_module':old is None}
  patch.extend(difflib.unified_diff([] if old is None else old.decode().splitlines(True),raw.decode().splitlines(True),fromfile='/dev/null' if old is None else 'a/'+rel,tofile='b/'+rel))
 (D/'overlay.patch').write_text(''.join(patch))
 (D/'SOURCE_MAP01.json').write_text(json.dumps({'schema_version':1,'baseline_commit':BASE,'files':result,'accepted_evidence':evidence,'typed_tail_activation_included':False},indent=2)+'\n')
 (D/'INVERSE_PROOF01.json').write_text(json.dumps({'schema_version':1,'edges':proofs,'new_modules_removed_on_inverse':[k for k,v in result.items() if v['new_module']]},indent=2)+'\n')
 print(json.dumps({'files':len(result),'new_modules':sum(v['new_module'] for v in result.values()),'literal_inverse_edges':len(proofs)}))
if __name__=='__main__':build()
