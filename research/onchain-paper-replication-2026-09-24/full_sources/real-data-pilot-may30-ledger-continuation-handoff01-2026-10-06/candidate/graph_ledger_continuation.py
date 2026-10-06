"""Fresh registered May30 graph-only continuation from a recovered closed ledger.
Original FAILED parent, source completion and partial arrays remain untouched.
"""
import hashlib,json,os,stat
from pathlib import Path
OLD='eth-paper-real-pilot-graph-20220530-20261005-01'
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/sources'
WEEK='2022-05-30T00:00:00Z';END='2022-06-06T00:00:00Z'
LEDGER=PREFIX+'/'+OLD+'/aggregation/ledger.sqlite'
FIXED={'daily_map_00': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-05-30.json', 'sha256': '660b15be6566348a4ef02535d61233f723e3e92f90c3eab2c4d9dcbde9d87369'}, 'daily_map_01': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-05-31.json', 'sha256': 'd4e874245dfa837cf2e1f95bf38e7f72795563d791e8bdbf618f5ab8084a4dbe'}, 'daily_map_02': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-06-01.json', 'sha256': '7bfed58757317901da16deffadd5b27cd70fcbd355b7479b157a1d6f62afe0e1'}, 'daily_map_03': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-06-02.json', 'sha256': '6f1783bd491641bb494ad2253b59d73c7fbccda128524187686df1b145a0ff3a'}, 'daily_map_04': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-06-03.json', 'sha256': '762fa53170c105fd73a35e23c0e877f9b68c3a4ad96309399dee5b89d6f30cdd'}, 'daily_map_05': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-06-04.json', 'sha256': '25bbfd679edb6153e4678707f9addc7569ec4d8ae13a9598ae05d4cc55d660af'}, 'daily_map_06': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/daily-maps/2022-06-05.json', 'sha256': '30b497fa33cdc68b292789a971b83024ade8e5cbcf2ecb1bde515046415a4ec6'}, 'graph_config': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/config/graph.json', 'sha256': 'c91f8eeb1d317a310ef0f90f40a78ccf60bdd2437532f5e909f7dfd079d7fc20'}, 'graph_plan': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-end-to-end-pilot-preparation01-2026-10-05/graph-stages-draft01/2022-05-30.json', 'sha256': '4ebe10b3a0ed0dda628515084bf9b8bfff8576d1f49bf2c5dccdb65d35990cf8'}, 'old_aggregation_intent': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/intent.json', 'sha256': '70c399143f832ff88610645f873d5709e4aa13d185f08b02d15d51b70779cd97'}, 'old_boundary_0': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000000.json', 'sha256': 'a3a1ce7fe54cc82147c1dc13d8390b7996e739f2eeffd89b7333115b60115839'}, 'old_boundary_1': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000001.json', 'sha256': '35f462f928975092760b2405751a150ccff5ab24319f48ff3d3754270b651385'}, 'old_boundary_2': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000002.json', 'sha256': 'df4903bc8a5338bc85093a6940fa57f9ba8a5d559b54b4dea1e35af2de5943d8'}, 'old_boundary_3': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000003.json', 'sha256': 'f5364edb42ae92617c260fb1dbebc151e1cd8a32fa2474222d80fb2f9ad3c66d'}, 'old_boundary_4': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000004.json', 'sha256': '737fafda2ab430d1c2128fd03faf8825278edbd865bf5d0d8602cffb515734e0'}, 'old_boundary_5': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000005.json', 'sha256': '021489d4972d060e0f5f7416b8a023ba9265f18bef2c4c886ea743fd38f79b64'}, 'old_boundary_6': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/aggregation/source-000006.json', 'sha256': '0dfc5fbc66a97554f5d3853ebd1c8d9505e891309f6fe07a73aa82dea6ebb398'}, 'old_claim': {'dataset': 'eth', 'path': 'research_runs/eth-paper-real-pilot-graph-20220530-20261005-01/claim.json', 'sha256': '63e94692f690373cc238bbb7d7c7e5147129f145c8df18b650a1040736b50a76'}, 'old_failed': {'dataset': 'eth', 'path': 'research_runs/eth-paper-real-pilot-graph-20220530-20261005-01/failed.json', 'sha256': 'f5e452d0352424a13db233a914ffb1ce742244a49de0481ef1b011459b2b569b'}, 'old_graph_intent': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/intent.json', 'sha256': '66497ac8b8c77ae3fc3ab9b54cd1ab0467f0ec1a5cb02775d6fa3bf2ad7024e7'}, 'old_root_terminal': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph01-2026-10-06/ROOT_TERMINAL01.json', 'sha256': '498bee3919eee4a79d3b983746cd5f0090963780b58e272128b5a70f3548cc1a'}, 'old_source_cell': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/source-000000.json', 'sha256': 'cc04e73e0d4a56e7162606a22e2d0e9607d1c088a230dc6a8a55aa65a8748ae3'}, 'old_source_coverage': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/source-coverage.json', 'sha256': '3edfc6acf292ac62454716b5a7f35acae70f2d9275b31117c69c0ecb42f0b9fb'}, 'weekly_source': {'dataset': 'eth', 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/historical-raw-to-population-reuse01-2026-10-05/weekly-inputs/2022-05-30.json', 'sha256': 'cc63156662073453a248a3918e7a47492a5c9bb59eb840e7ef53aa5f37fd8ad9'}, 'old_native_final': {'dataset': 'eth', 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-pilot-graph-20220530-20261005-01/guard/final.json', 'sha256': '8cfef38cd9fc43484742fcb61b5440e1eac8909ff46389793d2a3c770d12f823'}}

def need(v,m):
    if not v:raise ValueError('May30 retained ledger: '+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def plan_check(p):
    need(type(p) is dict and set(p)=={'schema_version','mode','asset','week','end_utc','predecessor','graph_config_input','ledger','recovery_review_input','original_inputs','new_experiment_id'},'exact plan fields')
    need(p['schema_version']==1 and p['mode']=='retained-ledger' and p['asset']=='ETH' and p['week']==WEEK and p['end_utc']==END and p['predecessor']==OLD,'fixed continuation scope')
    need(type(p['new_experiment_id']) is str and p['new_experiment_id'] and p['new_experiment_id']!=OLD,'fresh independently registered identity unbound')
    need(p['graph_config_input']=='graph_config' and p['original_inputs']=={k:k for k in FIXED},'original role selection differs')
    l=p['ledger'];need(type(l) is dict and set(l)=={'path','bytes','sha256'} and l['path']==LEDGER and type(l['bytes']) is int and l['bytes']==3189231616,'fixed ledger descriptor differs')
    need(type(l['sha256']) is str and len(l['sha256'])==64 and all(c in '0123456789abcdef' for c in l['sha256']),'actual recovered ledger SHA unbound')
    need(type(p['recovery_review_input']) is str and bool(p['recovery_review_input']),'actual independent recovery review unbound')
    return p

def original_metadata(read):
    raw={k:read(k) for k in FIXED}
    need(all(type(v) is bytes and len(v)<=2*1024**2 and sha(v)==FIXED[k]['sha256'] for k,v in raw.items()),'original metadata bytes differ')
    v={k:json.loads(b) for k,b in raw.items()};claim=v['old_claim'];failed=v['old_failed'];intent=v['old_graph_intent'];cell=v['old_source_cell'];coverage=v['old_source_coverage'];ag=v['old_aggregation_intent']
    need(claim['experiment_id']==failed['experiment_id']==OLD and failed['status']=='failed' and failed['claim_sha256']==sha(raw['old_claim']) and failed['output_sha256']=={},'original failed claim differs')
    need(intent['claim_sha256']==failed['claim_sha256'] and intent['source_commit']==claim['source']==claim['design_source'] and intent['plan_sha256']==claim['inputs']['graph_plan']['sha256']==coverage['plan_sha256'],'source intent joins differ')
    need(cell=={'id':'source-000000','input':'weekly_source','manifest_sha256':claim['inputs']['weekly_source']['sha256'],'rows':7507236,'status':'complete'},'actual source completion differs')
    need(claim['inputs']['weekly_source']==FIXED['weekly_source'] and claim['inputs']['graph_config']==FIXED['graph_config'],'original input binding differs')
    config=v['graph_config'];need(ag['binding']=={'asset':'ETH','coverage':[[WEEK,END]],'graph_config':config} and ag['continuation']=='new admitted identity required; reopening forbidden','aggregation intent differs')
    members=coverage['members'];need(len(members)==7 and len(v['weekly_source']['members'])==7,'seven-source denominator differs')
    total=0;checkpoints=[]
    for i,m in enumerate(members):
        b=v['old_boundary_'+str(i)];total+=m['expected_rows']
        need(b=={'sequence':i,'source_hash':m['sha256'],'rows':m['expected_rows'],'total_rows':total},'boundary commit marker differs')
        need(m['sha256']==FIXED[f'daily_map_{i:02d}']['sha256'] and m['source_manifest_sha256']==cell['manifest_sha256'],'daily source identity differs')
        checkpoints.append((i,b['source_hash'],b['rows'],b['total_rows']))
    need(total==7507236,'source count differs')
    root=v['old_root_terminal'];guard=v['old_native_final']
    need(root['identity']==OLD and root['actual_root_tool_exit_code']==root['actual_parent_exit_code']==1 and root['selected_recorded_pids_absent'] is True and root['actual_current_cgroup_absent'] is True and root['guard_final_sha256']==sha(raw['old_native_final']),'actual failed parent closure differs')
    need(guard['phase']=='failed' and guard['child_exit_code']==125 and guard['cleanup_verified'] is True,'original native failure differs')
    return v,checkpoints

def _sig(s):return (s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode))

def produce(run,plan_input):
    from tradingagents.research.lifecycle import ResearchRun,_immutable
    need(type(run) is ResearchRun,'genuine fresh ResearchRun required')
    run._active();run._check_source();p=plan_check(json.loads(run.read_input(plan_input)))
    need(run.admission.experiment_id==p['new_experiment_id'] and run.admission.experiment['cells']==['graph-2022-05-30'],'fresh graph-only registered denominator differs')
    for role,ref in FIXED.items():need(all(run.admission.inputs[role].get(k)==v for k,v in ref.items()),'registered original input differs: '+role)
    v,checkpoints=original_metadata(run.read_input)
    recovery=json.loads(run.read_input(p['recovery_review_input']))
    need(recovery.get('decision')=='accepted' and recovery.get('predecessor')==OLD and recovery.get('parent_status')=='failed' and recovery.get('ledger_byte_recovery') is True and recovery.get('ledger')==p['ledger'] and recovery.get('committed_source_rows')==7507236 and recovery.get('source_boundary_count')==7,'actual independently reviewed ledger recovery required')
    root=run.admission.root;guard=v['old_native_final']
    need(not Path(guard['cgroup']).exists() and all(type(pid) is int and pid>0 and not Path('/proc',str(pid)).exists() for pid in v['old_root_terminal']['actual_selected_recorded_pids']),'old selected producer still present')
    from .resources import assert_guarded_worker
    import sys
    job=json.loads(run.read_input('execution_job'));limits=job['resources']
    need(job['kind']=='graphs' and job['payload']=={'plan_input':plan_input},'genuine graph job differs')
    assert_guarded_worker(root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/run.admission.experiment_id/'guard',sys.orig_argv,required_paths=[root],wall_seconds=limits['wall_seconds'],memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'],disk_floor_bytes=limits['disk_floor_bytes'])
    from .provenance import file_hash,durable_mkdir,sync_directory
    path=root/LEDGER;before=path.lstat()
    need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==p['ledger']['bytes'],'original ledger path/extent differs')
    need(all(not Path(str(path)+s).exists() and not Path(str(path)+s).is_symlink() for s in ('-journal','-wal','-shm')),'unsealed SQLite sidecar present')
    need(file_hash(path)==p['ledger']['sha256'],'recovered ledger body differs')
    need(_sig(path.lstat())==_sig(before),'ledger changed during initial hash')
    directory=root/PREFIX/run.admission.experiment_id;durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    _immutable(directory/'intent.json',{'claim_sha256':run._claim_sha256,'source_commit':run.admission.source,'plan_sha256':run.admission.inputs[plan_input]['sha256'],'predecessor':OLD,'predecessor_status':'failed','ledger':p['ledger'],'source_rows_inherited':7507236,'no_source_reingestion':True})
    import sqlite3
    from urllib.parse import quote
    from .weekly_retained_ledger import graphs_from_ledger
    from .graph_store import save_graph
    from .graph_production import _verify_graph_coverage
    from .cache import cache_key
    db=None;iterator=None;record=None;reason=None;primary=None;graphs={}
    try:
        db=sqlite3.connect('file:'+quote(str(path),safe='/')+'?mode=ro',uri=True)
        db.execute('PRAGMA cache_size=-32768');db.execute('PRAGMA temp_store=FILE');db.execute('BEGIN')
        need(db.execute('PRAGMA integrity_check').fetchall()==[('ok',)],'SQLite integrity failed')
        need(db.execute('SELECT sequence,source,rows,total_rows FROM source_checkpoints ORDER BY sequence').fetchall()==checkpoints,'DB checkpoints differ from committed metadata')
        need(db.execute('SELECT count(*) FROM events').fetchone()==(7507236,),'ledger event denominator differs')
        need(db.execute('SELECT source,count(*) FROM events GROUP BY source ORDER BY source').fetchall()==sorted((r[1],r[2]) for r in checkpoints),'event/source denominator differs')
        need(db.execute('SELECT DISTINCT asset,week FROM events ORDER BY asset,week').fetchall()==[('ETH',WEEK)],'ledger week/asset differs')
        need([r[2] for r in db.execute('PRAGMA index_info(week_category)')]==['asset','week','category'],'original committed index unavailable')
        iterator=graphs_from_ledger(db,v['graph_config'],[[WEEK,END]])
        graph=next(iterator)
        need(graph.asset=='ETH' and graph.start_utc==WEEK and graph.end_utc==END and graph.raw_count==7507236,'continued graph extent differs')
        dest=save_graph(directory/'graph-2022-05-30',graph)
        try:next(iterator)
        except StopIteration:pass
        else:raise ValueError('extra graph from retained ledger')
        # Rejoin the exact original bytes before acknowledging new graph completion.
        need(file_hash(path)==p['ledger']['sha256'] and _sig(path.lstat())==_sig(before),'original ledger changed during continuation')
        run._active();run._check_source()
        proof={'schema_version':1,'asset':'ETH','week':WEEK,'end_utc':END,'graph_config_hash':cache_key(v['graph_config']),'graph_manifest_sha256':file_hash(dest),'claim_sha256':run._claim_sha256,'plan_sha256':run.admission.inputs[plan_input]['sha256'],'members':v['old_source_coverage']['members']}
        _verify_graph_coverage(proof,graph,proof['graph_manifest_sha256'])
        coverage_path=dest.parent/'coverage.json';_immutable(coverage_path,proof)
        record={'id':'graph-2022-05-30','status':'complete','manifest_path':str(dest.relative_to(root)),'manifest_sha256':proof['graph_manifest_sha256'],'raw_count':graph.raw_count,'admitted_count':graph.admitted_count,'exclusion_counts':dict(graph.exclusion_counts),'source_hashes':list(graph.source_hashes),'coverage_path':str(coverage_path.relative_to(root)),'coverage_sha256':file_hash(coverage_path),'continued_from':OLD,'source_rows_redecoded':0}
        graphs[WEEK]={k:x for k,x in record.items() if k not in ('id','status')}
    except Exception as error:
        primary=error;reason=type(error).__name__+': '+str(error)
    finally:
        try:
            if iterator is not None:iterator.close()
            if db is not None:db.close()
        except BaseException as cleanup:
            if primary is not None:
                primary.add_note('continuation cleanup also failed: '+repr(cleanup))
                raise primary from cleanup
            raise
    if record is None:record={'id':'graph-2022-05-30','status':'unavailable','reason':reason or 'no durable continuation disposition'}
    _immutable(directory/'graph-2022-05-30.json',record)
    summary={'asset':'ETH','expected_weeks':[WEEK],'graphs':graphs,'reason':reason,'predecessor':OLD,'predecessor_status':'failed','source_rows_inherited':7507236,'source_rows_redecoded':0,'workspace':None,'financial_run_admitted':False,'qualification':'Fresh graph-only continuation; original failed claim and partial graph unchanged. Registered recovered bytes and DB checkpoints were checked; no source rerun or Owner capability synthesized.'}
    _immutable(directory/'result.json',summary)
    return [record],summary,directory
