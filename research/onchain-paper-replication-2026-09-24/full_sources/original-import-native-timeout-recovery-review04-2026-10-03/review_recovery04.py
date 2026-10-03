"""Independent offline readback of retained remote objects/recovered bodies; no fetch."""
import hashlib,json,os,stat,subprocess,tarfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation06-2026-10-03';REC=P/'outcome-recovery01';CAP=REC/'recovered-terminal-capsule04';BARE=REC/'repository.git';ID='original-import-native-success-20261003-04'
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def doc(p):return json.loads(p.read_text())
def git(where,*args):return subprocess.check_output(['git',*args],cwd=where,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20)
def batch(where,commit,pins):
 names=sorted(pins);wire=subprocess.check_output(['git','cat-file','--batch'],cwd=where,input=''.join(commit+':'+n+'\n' for n in names).encode(),env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20);offset=0
 for n in names:
  e=wire.index(b'\n',offset);fields=wire[offset:e].split();assert len(fields)==3 and fields[1]==b'blob';size=int(fields[2]);assert size<=4194304;offset=e+1;body=wire[offset:offset+size];assert digest(body)==pins[n];offset+=size;assert wire[offset:offset+1]==b'\n';offset+=1
 assert offset==len(wire)
def main():
 report=doc(P/'REMOTE_PRIMARY_RECOVERY01.json');commit=report['remote_commit'];assert commit=='e5079ce3aae9f09cb2b1dc67d113568c15cd39ae';assert git(BARE,'rev-parse','FETCH_HEAD').decode().strip()==commit
 assert len(report['selected_blobs'])==52 and len({r['path'] for r in report['selected_blobs']})==52;selected={}
 for r in report['selected_blobs']:
  b=git(BARE,'show',commit+':'+r['path']);assert len(b)==r['bytes'] and digest(b)==r['sha256'];selected[Path(r['path']).name]=b
 meta=json.loads(selected['RETAINED_PRIMARY01.json']);release=json.loads(selected['release01.json']);execution=json.loads(selected['EXECUTION_PRIMARY01.json']);original=json.loads(selected['original_inputs01.json'])
 assert digest(selected['RETAINED_PRIMARY01.json'])==execution['retention_sha256'];archive=REC/'retained-primary01.tar.gz';assert archive.read_bytes()==selected['retained-primary01.tar.gz'];assert sha(archive)==meta['archive_sha256']==report['archive_sha256']
 rows={r['path']:r for r in meta['members']};assert len(rows)==1058;seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for t in tar:
   assert t.name=='capsule04' or t.name.startswith('capsule04/');name='.' if t.name=='capsule04' else t.name[10:];assert name in rows and name not in seen;seen.add(name);r=rows[name];p=CAP/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==t.mode==r['mode']
   if r['kind']=='directory':assert t.isdir() and stat.S_ISDIR(s.st_mode)
   else:
    assert t.isfile() and stat.S_ISREG(s.st_mode) and t.size==s.st_size==r['bytes'];assert sha(p)==r['sha256'];h=hashlib.sha256();f=tar.extractfile(t)
    for chunk in iter(lambda:f.read(65536),b''):h.update(chunk)
    assert h.hexdigest()==r['sha256']
 assert seen==set(rows);actual={'.'}
 for parent,dirs,files in os.walk(CAP,followlinks=False):
  actual.update(str((Path(parent)/n).relative_to(CAP)) for n in dirs+files)
 assert actual==seen and sum(r['bytes'] for r in rows.values())==7301050;assert sum(r['kind']=='file' for r in rows.values())==750
 assert git(CAP,'rev-parse','HEAD').decode().strip()==release['capsule_commit']==report['capsule_head'];assert len(release['source_files'])==162
 batch(CAP,release['capsule_commit'],release['source_files']);batch(CAP,release['source_anchor'],release['source_files'])
 for n,h in release['source_files'].items():assert sha(CAP/n)==h
 assert sha(CAP/release['registration'])==release['registration_sha256']
 assert len(original['inputs'])==11 and len(original['original_source_files'])==26
 for row in original['inputs']:assert sha(CAP/row['capsule_path'])==row['sha256']
 batch(CAP,original['original_source'],{n:r['claim_sha256'] for n,r in original['original_source_files'].items()})
 histories=[]
 for index,old in enumerate(report['historical_failed_claims'],1):
  run=CAP/'research_runs'/old['identity'];claim=doc(run/'claim.json');terminal=doc(run/'failed.json');assert sha(run/'claim.json')==old['claim_sha256']==terminal['claim_sha256'] and sha(run/'failed.json')==old['terminal_sha256'];assert terminal['status']=='failed' and not(run/'complete.json').exists();assert claim['effective_attempt_budget']==index+1
  assert len(claim['experiment']['source_files'])==[153,156,159][index-1];batch(CAP,claim['source'],claim['experiment']['source_files'])
  registration=git(CAP,'show',claim['source']+':'+claim['registration']);assert digest(registration)==claim['registration_sha256'] and json.loads(registration)['experiments'][old['identity']]==claim['experiment']
  outputs={f.name:sha(f) for f in (run/'outputs').iterdir()};assert outputs==terminal['output_sha256']==old['outputs'];assert len(outputs)==[4,4,2][index-1];histories.append({'identity':old['identity'],'source_count':len(claim['experiment']['source_files']),'output_count':len(outputs)})
 run=CAP/'research_runs'/ID;claim=doc(run/'claim.json');terminal=doc(run/'failed.json');assert sha(run/'claim.json')==report['claim_sha256']==terminal['claim_sha256'];assert sha(run/'failed.json')==execution['terminal_sha256'];assert terminal['status']=='failed' and claim['effective_attempt_budget']==5 and not(run/'complete.json').exists()
 assert claim['source']==release['capsule_commit'] and claim['registration_sha256']==release['registration_sha256'];assert claim['experiment']==doc(CAP/release['registration'])['experiments'][ID]
 for r in claim['experiment']['inputs'].values():assert sha(CAP/r['path'])==r['sha256']
 outputs={f.name:sha(f) for f in (run/'outputs').iterdir()};assert outputs==report['output_hashes']==terminal['output_sha256'] and set(outputs)=={'resource-binding.json'}
 assert report['missing_registered_outputs']==['cell-ledger.json','resource-journal.json','resource-summary.json'] and all(not(run/'outputs'/n).exists() for n in report['missing_registered_outputs'])
 cells=[]
 for r in report['source_cell_evidence']:
  assert sha(CAP/r['evidence']['path'])==r['evidence']['sha256'];v=doc(CAP/r['evidence']['path']);assert v==r['original_durable_record'];cells.append(v)
 assert cells==report['cell_dispositions'] and [c['status'] for c in cells]==['failed','unavailable']
 runroot=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;assert doc(runroot/'postmortem-cells.json')==cells
 roots=list((CAP/'research_artifacts/onchain_representations').glob('*/'+ID));assert len(roots)==1;rep=roots[0];assert (rep/'failed.json').exists() and not(rep/'complete.json').exists();assert sha(rep/'compact/dictionary-import/import-complete.json')==execution['original_dictionary_import_complete_sha256'];assert len(list(rep.glob('compact/mcm-*')))==1 and not list(rep.glob('compact/mcm-*/stage-complete.json'))
 outer=CAP/'fixture_outer'/ID;assert doc(outer/'terminal.json')['proof'] is None and doc(outer/'terminal.json')['status']=='failed';assert doc(outer/'cleanup.json')==execution['original_outer_cleanup'];assert execution['actual_selected_raw_authentication_error']['message']=='child terminal snapshot failed/missing';assert doc(runroot/'guard/final.json')['child_exit_code'] is None and doc(runroot/'guard/child_exit.json')['exit_code']==125
 return {'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'accepted-offline-readback-of-actual-remote-recovery','remote_commit':commit,'selected_remote_blobs':52,'members':1058,'files':750,'directories':308,'logical_bytes':7301050,'current_and_anchor_source_bodies':162,'original_git_paths':26,'original_json':11,'histories':histories,'current_outputs':outputs,'missing_outputs':report['missing_registered_outputs'],'current_input_count':len(claim['experiment']['inputs']),'completed_mcm':0,'disposition':'failed','no_live_absence_or_runtime_inferred':True}
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
