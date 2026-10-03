"""Exact actual request and unchanged launcher.validate only; no launch."""
import hashlib,importlib.abc,importlib.util,json,os,pathlib,shutil,stat,subprocess,sys,time
P=pathlib.Path(__file__).resolve().parent;F=P.parent;A=F/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';sha=lambda b:hashlib.sha256(b).hexdigest();assert pathlib.Path.cwd()==C
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
def read(n,h=None):
 b=(A/n).read_bytes()
 if h:assert sha(b)==h
 return json.loads(b)
q=read('COMPARE_REQUEST02.json','bd28fd97ccfb7457a3ae85ba743ee28963e1be23cf78d0b24330ee14161d18e3');c=read('EXACT_COMMAND02.json','bccdb2e53982303f5e3b49d424810ce2ae52b61221c6715dd81ca4e4d9bc1272');p=read('PARENT_COMMAND02.json','0860df9e81881f5e5adc1f8a9e1340f7d4907311be2d94c0bb4373998d3c946f')
assert q['source']==B and q['phase']=='compare' and c['allowed_identity']=='compact-cold-comparison-20261003-01';assert q['capsule']==c['cwd']==p['cwd']==str(C)
assert q['output_parent']==c['selected_once_global_output_parent']=='/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003'
assert c['argv']==[sys.executable,'-B',c['launcher']['path'],'--request',str(A/'COMPARE_REQUEST02.json'),'--request-sha256',sha((A/'COMPARE_REQUEST02.json').read_bytes())]
assert p['argv']==[sys.executable,'-B',p['parent_source']['path'],'--command',str(A/'EXACT_COMMAND02.json'),'--command-sha256',sha((A/'EXACT_COMMAND02.json').read_bytes()),'--output',str(A/'actual-parent-wait01')]
assert p['actual_parent_output']==str(A/'actual-parent-wait01') and not os.path.lexists(p['actual_parent_output'])
assert sha(pathlib.Path(p['parent_source']['path']).read_bytes())==p['parent_source']['sha256']=='424e77b8ef2e1b199232b9efcbacbb5dba6ce8c825baf74b89407b449b7b68a5';assert sha(pathlib.Path(c['launcher']['path']).read_bytes())==c['launcher']['sha256']=='3eb3c7f578c7b1308992cda0d8f3bea7ca98ed42ae97ad578590e7e993b4ad6a'
assert len(q['known_processes'])==len(set(q['known_processes']))==23;assert all(not pathlib.Path('/proc',str(pid)).exists() for pid in q['known_processes'])
for ref in list(q['reviews'].values())+[c['launcher_review']]:assert sha(pathlib.Path(ref['path']).read_bytes())==ref['sha256']
assert set(q['reviews'])=={'composition','registration','release','recovery','withdrawal'}
# Entire index independent exact body/membership check, root intentionally omitted.
index=json.loads(pathlib.Path(q['recovery']['path']).read_bytes());assert sha(pathlib.Path(q['recovery']['path']).read_bytes())==q['recovery']['sha256'];assert index['source']==B and index['original_root']==str(C);other=pathlib.Path(index['recovered_root']);assert other!=C
rows=index['members'];assert len(rows)==973 and len({r['path'] for r in rows})==973;assert sum(r['kind']=='file' for r in rows)==706 and sum(r['kind']=='directory' for r in rows)==267
for base in [C,other]:
 actual=[]
 for root,dirs,files in os.walk(base,followlinks=False):
  for name in dirs+files:actual.append(str((pathlib.Path(root)/name).relative_to(base)))
 assert sorted(actual)==sorted(r['path'] for r in rows)
 for r in rows:
  path=base/r['path'];s=path.lstat();assert path.resolve()==path
  if r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  else:
   assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;raw=path.read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256']
assert sum(r.get('bytes',0) for r in rows)==5931010
# Install independent import blocker before the single module load/validate.
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}:raise RuntimeError('review numerical imports prohibited')
sys.meta_path.insert(0,Block());spec=importlib.util.spec_from_file_location('review_launcher02',c['launcher']['path']);launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
started=time.monotonic();root,release,ctx,resources,recovered,relpath=launcher.validate(q);elapsed=time.monotonic()-started
assert root==C and release['source']==B and relpath=='cold_release/compare02/released-envelope02.json';assert len(ctx['sources'])==195 and len(ctx['experiment']['inputs'])==44 and len(ctx['runtime']['distribution_records'])==251;assert ctx['family']['attempt_budget']==2 and ctx['family']['prior_attempts']==0
assert not os.path.lexists(p['actual_parent_output']) and not os.path.lexists(pathlib.Path(q['output_parent'])/c['allowed_identity'])
old_collection=F/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03/COLLECTION_REQUEST01.json';plan=json.loads(old_collection.read_bytes())['reservation_roots']['compare'];assert plan=={'parent':p['actual_parent_output'],'wrapper':str(pathlib.Path(q['output_parent'])/c['allowed_identity'])}
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for n in sys.modules)
result={'schema_version':1,'decision':'accepted-exact-prospective-comparison-request-and-parent-pending-external-bundle-and-fresh-final-eligibility','request_sha256':sha((A/'COMPARE_REQUEST02.json').read_bytes()),'command_sha256':sha((A/'EXACT_COMMAND02.json').read_bytes()),'parent_command_sha256':sha((A/'PARENT_COMMAND02.json').read_bytes()),'source_B2':B,'installed_release_sha256':q['release']['sha256'],'index_nonroot_members':973,'root_inclusive_members':974,'files':706,'directories_including_root':268,'logical_bytes':5931010,'both_complete_trees_verified':True,'mode_preservation_scope':'separate accepted whole-capsule recovery c91bc4b9','known_pid_absences':23,'original_collector_parent_wrapper_paths_match':True,'source_count':195,'package_count':147,'input_roles':sorted(ctx['experiment']['inputs']),'runtime_records':251,'cpus':release['cpus'],'family':ctx['family'],'validate_seconds':elapsed,'mem_available_after_bytes':resources.mem_available(),'disk_free_after_bytes':shutil.disk_usage(C).free,'cpu_affinity':sorted(os.sched_getaffinity(0)),'exact_five_reviews':q['reviews'],'selected_global_output_parent':q['output_parent'],'launch_or_reservation_or_numerical_import':False}
(P/'READBACK02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
