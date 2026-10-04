from pathlib import Path
import os,stat,json,hashlib,types,time
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-wrapper-compatibility-coalesced-evidence-correction04-2026-10-04';O=F/'financial-wrapper-compatibility-coalesced-evidence-root03-2026-10-04';L=F/'financial-wrapper-compatibility-coalesced-evidence-root-launch04-2026-10-04';R=F/'financial-wrapper-compatibility-composed-recovery-review02-2026-10-04';A=F/'financial-wrapper-compatibility-coalesced-evidence-source-review04-2026-10-04';checks=[];reads={};start=time.monotonic()
def h(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def sig(s):return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def read(p,pin=None):
 p=Path(p);s=p.lstat();ok(p.is_absolute() and p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded singlelink ordinary read');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);b=b''
 try:
  ok(sig(os.fstat(fd))==sig(s),'opened descriptor join')
  while c:=os.read(fd,65536):b+=c;ok(len(b)<=4194304,'actual individual extent')
  ok(sig(os.fstat(fd))==sig(s),'last descriptor join')
 finally:os.close(fd)
 ok(sig(p.lstat())==sig(s) and len(b)==s.st_size,'current byte extent');ok(pin is None or h(b)==pin,'exact body hash');reads[str(p)]={'sha256':h(b),'bytes':len(b),'mode':stat.S_IMODE(s.st_mode),'signature':sig(s)};ok(time.monotonic()-start<60,'bounded review time');return b
def J(p,pin=None):return json.loads(read(p,pin))
source=read(P/'copy_layout01.py','fcadbfcde1bf9d9d61887af27de2dff610b5d7cce188a4cb77da1c99d6989fda');spec=J(P/'INPUTS01.json','5c4c9ebbc976d057a1896f106c18fc00c8c0a179e2beaf047bc5ed329ea40f04');release=J(A/'MACHINE01.json','cfe4f31b946125d0f484ac7b547b9cb8418e736df5e5f605e112a1f101effdfc');release_seal=J(A/'MANIFEST01.json','0d1c862775f1dfec4bdde55249837fab13593321f9b8d3575ed678ece1794de3');read(A/'REPORT01.md',release['report_sha256']);ok(release['decision']=='ACCEPTED_EXACT_ONE_USE_ROOT_METADATA_COPY_ONLY' and release['source_sha256']==h(source) and release['inputs_sha256']==h(read(P/'INPUTS01.json')) and release['fixed_root']==str(O),'genuine exact source release')
intent=J(L/'INTENT01.json','02726ab0780c60c68c2c88729adcf7723e48782440acd6bfc9ce84e872147684');spawn=J(L/'SPAWN01.json','ad98e65079455b2f61ebe1c43a5f8b1f4d2b51b9ccd2bb29b29cd9e6ecedafb1');child=J(L/'ACTUAL_CHILD_EXIT01.json','e052dde3dc56af1983f0b952463a37bb14dc39a432dab4df6fa58bdcfba33986');tool=J(L/'ACTUAL_ROOT_TOOL_EXIT01.json','3a21e1f0088e8035b96a15672dfdd4a4174d71c1259543ab68bcaf190cb5157c')
for ref in (intent['source'],intent['inputs'],intent['release'],tool['child_exit_receipt'],child['stdout'],child['stderr']):read(Path(ref['path']),ref['sha256'])
stdout=J(L/'stdout01.log',child['stdout']['sha256']);ok(read(L/'stderr01.log')==b'','empty actual stderr');ok(intent['command']==['/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python','-B',str(P/'copy_layout01.py')] and intent['output_root']==str(O),'actual exact command/output');ok(child['child_returncode']==tool['actual_tool_root_exit']==0 and child['reaped'] is True and child['timed_out'] is False and spawn['child_pid']==spawn['child_pgid']==child['child_pid']==1100653,'actual reaped child/root zero');ok(tool['actual_tool_chunk_id']=='7fe463' and stdout['Root_exit'] is None and child['actual_tool_root_exit'] is None,'original NULLs and separate actual exit retained');ok(not Path('/proc/1100653').exists(),'actual PID absent now')
pgrps=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:
   b=(p/'stat').read_bytes();ok(len(b)<16384,'bounded process metadata');fields=b.rsplit(b')',1)[1].split()
   if fields[2]==b'1100653':pgrps.append(p.name)
  except (FileNotFoundError,ProcessLookupError):pass
ok(not pgrps,'sampled actual process group absent');ok(stdout['status']=='DRAFT_COPIED_NOT_AUTHORITY' and stdout['copied_regular_bodies']==57 and stdout['receipt_bodies']==38 and stdout['actual_bytes_read_including_full_finish']==7978780<8388608 and stdout['numerical_authority'] is False,'actual copier complete bounded draft')
base_seal=J(R/'MANIFEST01.json','4c1bafac000b164f4534e0308169214c9fd7f3f72cab2f4389a1647e6ada3cde');base=J(R/'MACHINE01.json','aae1d255e54bf8fb52a82c7c7dff6495df16e1c82b71d448828e28f841db116f');read(R/'REPORT01.md',base['report_sha256']);proof=J(R/'RECOVERY_PROOF01.json','c5cf38d2a54682e9b36c0d4462cc07a611fb047cc422803b23d590552511b7a5');closure=J(R/'CLOSURE01.json');actual_base=set()
for root,ds,fs in os.walk(R,followlinks=False):
 for n in ds+fs:
  rel=(Path(root)/n).relative_to(R).as_posix()
  if rel!='MANIFEST01.json':actual_base.add(rel)
for x in base_seal['members']:
 p=R/x['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==x['mode'],'original accepted seal mode')
 if x['kind']=='file':ok(len(read(p,x['sha256']))==x['bytes'],'original accepted seal body')
 else:ok(stat.S_ISDIR(s.st_mode),'original accepted seal directory')
ok(actual_base=={x['path'] for x in base_seal['members'] if x['path']!='.'},'complete accepted baseline seal');ok(base['decision']=='ACCEPTED_ACTUAL_OPERATIONAL_SOURCE_POLICY_BYTE_RECOVERY' and base['source_commit']=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c' and base['current_typed']==589 and base['protected_typed']==585 and base['complete_reachable_git_objects']==394,'exact original accepted7b589585394 recovery scope')
ok(len(spec['rows'])==57 and len(closure['provenance'])==51,'actual denominators57/51');fields=('path','original_path','sha256','bytes','original_mode','copy_mode');ok({tuple(x[k] for k in fields) for x in closure['provenance']}=={tuple(x[k] for k in fields) for x in spec['rows'] if x['role'] in ('receipt','source-evidence')},'exact51 historical origins')
for x in spec['rows']:
 for p,m in [(Path(x['path']),x['copy_mode']),(Path(x['original_path']),x['original_mode']),(O/x['destination'],x['output_mode'])]:ok(len(read(p,x['sha256']))==x['bytes'] and stat.S_IMODE(p.lstat().st_mode)==m,'actual original/retained/copied body and mode')
origin=J(O/'ORIGIN_MAP01.json');draft=J(O/'DRAFT_LAYOUT01.json');ok(origin['members']==spec['rows'] and origin['original_provenance_count']==51 and origin['receipt_count']==38 and origin['source_evidence_count']==13,'literal full origin mapping');ok(origin['source_review_manifest_sha256']==h(read(R/'MANIFEST01.json')),'origin prior review pin');expectedrefs=[{'path':str(O/x['destination']),'sha256':x['sha256']} for x in spec['rows'] if x['role']=='receipt'];ok(draft['receipt_candidates']==expectedrefs and len(expectedrefs)==38,'all38 exact genuine receipt paths');ok({(x['path'],x['sha256']) for x in base['recovery_receipts']}=={(x['path'],x['sha256']) for x in spec['rows'] if x['role']=='receipt'},'all prior38 actual recovery receipts preserved');ok(all(draft[k] is None for k in ('new_accepted_machine','new_accepted_report','new_review_manifest','final_parent','actual_root_exit','whole_preclaim8MiB_fit')),'original missing authority remains NULL');ok(read(O/'ORIGINAL_RECOVERY_PROOF01.json')==read(R/'RECOVERY_PROOF01.json'),'exact literal old proof no reissue')
M=types.ModuleType('pinnedcopier');M.__file__=str(P/'copy_layout01.py');exec(compile(source,M.__file__,'exec'),M.__dict__);reader=M.PC.Reader();mf=draft['review_reference_candidates']['manifest'];manifest=json.loads(reader.reference(mf))
for key in ('proof','machine','report'):M.PC._sealed(manifest,mf,draft['review_reference_candidates'][key],reader)
reader.finish();whole={};logical=0;allocated=O.lstat().st_blocks*512
for root,ds,fs in os.walk(O,followlinks=False):
 for n in ds+fs:
  p=Path(root)/n;rel=p.relative_to(O).as_posix();s=p.lstat();ok(stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode),'ordinary actual output member');ok(s.st_uid==os.getuid(),'actual output owner');whole[rel]=sig(s);allocated+=s.st_blocks*512
  if stat.S_ISREG(s.st_mode):logical+=s.st_size;read(p)
  else:ok(stat.S_IMODE(s.st_mode)==0o700,'output directory700')
expected={x['destination'] for x in spec['rows']}|{'ORIGIN_MAP01.json','DRAFT_LAYOUT01.json'}|{Path(x['destination']).parts[0] for x in spec['rows'] if len(Path(x['destination']).parts)>1};ok(set(whole)==expected and len(whole)==63 and whole==stdout['output_observation']['members'],'actual exact63 member stdout signatures');ok(sig(O.lstat())==stdout['output_observation']['root_signature'] and stat.S_IMODE(O.lstat().st_mode)==0o700,'actual originalroot identity');ok(logical==stdout['output_observation']['logical_bytes'] and allocated==stdout['output_observation']['allocated_bytes'],'actual output resource extents');v=os.statvfs(O);ok(logical<=67108864 and allocated<=100663296 and v.f_bavail*v.f_frsize>=10737418240,'actual wholecaps floor');ok(not any((O/n).exists() for n in ('MACHINE01.json','REPORT01.md','MANIFEST01.json')),'candidate destination names absent')
for p,x in list(reads.items()):ok(h(read(p))==x['sha256'],'all body rejoin')
for n,s in whole.items():ok(sig((O/n).lstat())==s,'final output whole fingerprint rejoin')
out={'checks':len(checks),'actual_output_root':str(O),'actual_root_exit':tool,'actual_child_exit':child,'actual_stdout':stdout,'copied_input_rows':spec['rows'],'original_baseline_machine':base,'actual_receipt_refs':expectedrefs,'whole_signatures':whole,'whole_logical':logical,'whole_allocated':allocated,'actual_free':v.f_bavail*v.f_frsize,'reads':reads,'inner_policy_seal_passed':True,'baseline_scope_source':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','current32d_recovery_proven':False,'newproof_issued':False};(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(len(checks),len(reads),logical,allocated)
