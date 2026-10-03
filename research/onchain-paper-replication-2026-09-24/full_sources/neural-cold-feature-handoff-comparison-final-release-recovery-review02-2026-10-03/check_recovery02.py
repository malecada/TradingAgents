"""Independent saved-body + already fetched Git recovery check; no network."""
import hashlib,json,os,pathlib,stat,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
ROOT=BASE.parents[2];A=BASE/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';REC=A/'final-release-recovery02';BARE=REC/'repository.git';SAVED=REC/'selected';COMMIT='a18f2d958b9946fc77168f0e305e183812b04e3c'
assert ROOT.name=='TradingAgents-audit-fixes'
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'}
def git(*args):
 r=subprocess.run(['git','-c','protocol.allow=never','--git-dir',str(BARE),*args],env=env,capture_output=True,timeout=10)
 assert r.returncode==0,(args,r.stderr[:500]);assert len(r.stdout)<=4*1024**2
 return r.stdout
sha=lambda b:hashlib.sha256(b).hexdigest()
receiptpath=A/'REMOTE_FINAL_RELEASE_RECOVERY02.json';receipt=json.loads(receiptpath.read_bytes());manifestpath=A/'SELECTED_RELEASE_BODIES02.json';body=manifestpath.read_bytes();manifest=json.loads(body);name=str(manifestpath.relative_to(ROOT))
assert receipt['status']=='fresh-actual-remote-final-release-bodies-recovered' and receipt['remote_commit']==COMMIT
assert git('rev-parse','FETCH_HEAD').decode().strip()==COMMIT
assert receipt['manifest']=={'path':name,'sha256':sha(body),'bytes':len(body)}
assert receipt['selected_blobs']==manifest['rows'];assert len(manifest['rows'])==123 and receipt['blobs_including_manifest']==124
rows=manifest['rows']+[receipt['manifest']];assert len({r['path'] for r in rows})==124
assert [r['path'] for r in manifest['rows']]==sorted(r['path'] for r in manifest['rows'])
actual=[]
for root,dirs,files in os.walk(SAVED,followlinks=False):
 for d in dirs:
  s=(pathlib.Path(root)/d).lstat();assert stat.S_ISDIR(s.st_mode)
 for f in files:actual.append(str((pathlib.Path(root)/f).relative_to(SAVED)))
assert sorted(actual)==sorted(r['path'] for r in rows)
currentdifferent=[];total=0;pin={}
for row in rows:
 n=row['path'];rel=pathlib.PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts and str(rel)==n
 p=SAVED/n;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];assert git('cat-file','-t',COMMIT+':'+n)==b'blob\n';assert git('show',COMMIT+':'+n)==b
 if (ROOT/n).read_bytes()!=b:currentdifferent.append(n)
 total+=len(b);pin[n]=row['sha256']
assert receipt['logical_bytes_without_manifest']==total-len(body) and total-len(body)<=64*1024**2
assert sha(body)=='bdfb66a97072e95d5a46232191d260b578bdbeb109c3442a8d3653f588a6968c'
assert not currentdifferent
must={'COMPARE_REQUEST02.json':'bd28fd97ccfb7457a3ae85ba743ee28963e1be23cf78d0b24330ee14161d18e3','EXACT_COMMAND02.json':'bccdb2e53982303f5e3b49d424810ce2ae52b61221c6715dd81ca4e4d9bc1272','PARENT_COMMAND02.json':'0860df9e81881f5e5adc1f8a9e1340f7d4907311be2d94c0bb4373998d3c946f','recover_release02.py':'b68870148fa6ada1ec04121b7716ea7179390362f9ec1e6489898d886c8f6060'}
for n,h in must.items():assert pin[str((A/n).relative_to(ROOT))]==h
savedA=SAVED/A.relative_to(ROOT);q=json.loads((savedA/'COMPARE_REQUEST02.json').read_bytes());c=json.loads((savedA/'EXACT_COMMAND02.json').read_bytes());p=json.loads((savedA/'PARENT_COMMAND02.json').read_bytes())
assert p['cwd']==c['cwd']==q['capsule'];assert p['argv'][2]==p['parent_source']['path'];assert p['argv'][4]==str(A/'EXACT_COMMAND02.json');assert p['argv'][6]==must['EXACT_COMMAND02.json'];assert p['argv'][8]==str(A/'actual-parent-wait01')
for ref in list(q['reviews'].values())+[p['parent_source'],c['launcher'],c['launcher_review']]:assert pin[str(pathlib.Path(ref['path']).relative_to(ROOT))]==ref['sha256']
assert p['parent_source']['sha256']=='424e77b8ef2e1b199232b9efcbacbb5dba6ce8c825baf74b89407b449b7b68a5'
assert c['launcher']['sha256']=='3eb3c7f578c7b1308992cda0d8f3bea7ca98ed42ae97ad578590e7e993b4ad6a'
requestreview=BASE/'neural-cold-feature-handoff-comparison-root-request-review02-2026-10-03/REVIEW_REQUEST02.md';assert pin[str(requestreview.relative_to(ROOT))]=='310d1f21a5c9a7fa75b9005702f7ef5d70626104ca1e9ec5786702cc7c6d6a72'
assert q['reviews']['recovery']['sha256']=='c91bc4b98031045737f53755842ff5df47a9ff858395dfbfe498c6454bbe7150'
assert q['reviews']['release']['sha256']=='40990e9733c0d3dce85fcf0d882c8f23f43c20e2e7b90b152fb664a153a7e49a'
assert q['reviews']['registration']['sha256']=='bcf5f2a84bb09b10b9d69a1d726b6e32e0fc626013271b8fbee6562cada06cb5'
assert 'c927fa20b3c32d6361905c4b49c959d29599979a8b664379aed7e3c91b4a8375' in pin.values()
assert 'cac6d1a678e85d814b7f62fcc7185140c8e95b3b80ed96abcf86c81e2c2cbcf0' in pin.values()
C=pathlib.Path(q['capsule']);B='361339125a3f1cd57e7ba8611f5a994ae649fa0b'
r=subprocess.run(['git','-c','protocol.allow=never','rev-list','--parents','-n','1','HEAD'],cwd=C,env=env,capture_output=True,timeout=10);assert r.returncode==0 and r.stdout.decode().strip().split()==[B,'9742c6ec817dd0917f9f35a52e4b83965ca1cd29']
assert q['source']==B and len(q['known_processes'])==len(set(q['known_processes']))==23 and all(not pathlib.Path('/proc',str(x)).exists() for x in q['known_processes'])
identity=c['allowed_identity'];absence=[C/ns/identity for ns in ['research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs']]+[pathlib.Path(q['output_parent'])/identity,pathlib.Path(p['actual_parent_output'])];assert all(not os.path.lexists(x) for x in absence)
assert q['output_parent']=='/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003'
native=subprocess.run(['systemctl','--user','list-units','--state=running','--plain','--no-legend','onchain-replication-*'],capture_output=True,timeout=10);assert native.returncode==0 and not native.stdout.strip();(HERE/'native_units02.txt').write_bytes(native.stdout);(HERE/'native_units02.stderr').write_bytes(native.stderr)
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
result={'receipt_sha256':sha(receiptpath.read_bytes()),'manifest_sha256':sha(body),'commit':COMMIT,'selected_files':124,'logical_without_manifest':total-len(body),'manifest_bytes':len(body),'logical_including_manifest':total,'saved_membership_exact':True,'all_objects_present_with_lazy_fetch_disabled':True,'all_bodies_and_hashes_match':True,'current_originals_different':currentdifferent,'exact_request_command_parent_launcher_and_reviews_match':True,'whole974_archive_and_retention_body_pins_present':True,'source_B2_unchanged':True,'known_pid_absences':23,'comparison_reservation_absences':[str(x) for x in absence],'running_onchain_native_units':0,'network_or_numerical_or_original_invocation':False}
(HERE/'READBACK02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
