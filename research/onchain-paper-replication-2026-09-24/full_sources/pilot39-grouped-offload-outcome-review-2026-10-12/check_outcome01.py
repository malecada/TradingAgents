from pathlib import Path
import json,hashlib,os
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'real-data-pilot-full39-entry-preparation01-2026-10-12';R=F/'pilot39-grouped-offload-outcome-review-2026-10-12';ID='eth-paper-real-data-end-to-end-resource-20261012-39';run=Path('research_runs')/ID;native=Path('research_artifacts/onchain-paper-replication-2026-09-24/runs')/ID;parent=native.parent.parent/'pilot-parent'/ID
E={}
def body(p):
 b=p.read_bytes();E[str(p)]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(body(p))
claim=js(run/'claim.json');failed=js(run/'failed.json');assert failed['claim_sha256']==E[str(run/'claim.json')] and failed['status']=='failed' and not (run/'complete.json').exists();assert claim['effective_attempt_budget']==110 and claim['experiment_id']==ID
outputs={}
for name,digest in failed['output_sha256'].items():
 p=run/'outputs'/name;outputs[name]=js(p);assert E[str(p)]==digest
s=outputs['pilot-summary.json'];t=s['throughput'];assert t['complete_graphs']==0 and t['failed_graphs']==1 and t['unavailable_graphs']==6 and s['training'] is None
assert all(x['completed_motif_cells'] is None and x['completed_nodes'] is None for x in t['graphs']);assert t['completed_motif_cells_per_second'] is None and t['one_update_phase_seconds'] is None
assert [x['status'] for x in t['graphs']]==['failed']+['unavailable']*6
assert outputs['cell-ledger.json']==js(native/'postmortem-cells.json')==[s['cell']]
guard=js(native/'guard/final.json');observer=js(native/'observer.json');owner=js(native/'owner.json');launch=js(native/'launch.json')
for path,digest in observer['evidence_sha256'].items():assert hashlib.sha256(body(native/path)).hexdigest()==digest
assert observer['owner_sha256']==E[str(native/'owner.json')] and observer['terminal_sha256']==E[str(run/'failed.json')]
assert guard['child_exit_code']==1 and guard['cleanup_verified'] is True and guard['elapsed_seconds']==11660.373778718
assert guard['memory_events']['oom']==guard['memory_events']['oom_kill']==0
assert guard['peak_sampled_memory_current_bytes']==5368414208
closed=js(D/'ROOT_IO_CLOSED01.json');storage=js(D/'FINAL_STORAGE01.json');assert closed['supervisor_pid']==owner['supervisor_pid']==launch['supervisor_pid']==745583 and closed['supervisor_reaped'] and closed['outer_log_handles_closed'] and closed['actual_parent_exit_code']==1
for k,p in [('guard',native/'guard/final.json'),('owner',native/'owner.json'),('launch',native/'launch.json')]:assert storage['original_metadata_sha256'][k]==E[str(p)]
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['actual_current_unit_properties']['MainPID']=='0'
log=body(native/'guard/child.log').decode();assert "stale interval cannot refresh" in log and 'typed_payload_operations.py", line 262' in log
note=json.loads(log.split('MCM delivery incomplete: ')[-1].splitlines()[0]);assert note['attempted_sink_cells']==note['journal_completed_cells']==65536 and note['confirmed_post_sink_cells']==61440
assert json.loads(body(parent/'stdout.log'))==observer and body(parent/'stderr.log')==b''
a=outputs['archive-terminal.json'];assert a['status']=='failed' and a['spent']['commands']==0 and a['wire_bytes_measured'] is False
stage=Path('research_artifacts/onchain_batched_offload/694a1655968edcb31f2589fee05be14243664967bed53d8d97470d22de609b54/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba');group=stage/'preserve/00000000';m=js(group/'manifest.json');assert (group/'manifest.json').stat().st_size==40329 and m['archive_bytes']==3532800 and len(m['members'])==m['files']==48
archive=body(group/'bundle.tar');assert len(archive)==m['archive_bytes'] and hashlib.sha256(archive).hexdigest()==m['archive_sha256'];assert sorted(p.name for p in stage.iterdir())==['preserve'] and sorted(p.name for p in group.iterdir())==['bundle.tar','manifest.json']
prior=F/'pilot39-local-prefix-progress-review-2026-10-12/RETURN_REVIEW01.json';assert hashlib.sha256(body(prior)).hexdigest()=='bceee514b429219aeadd32f53137582c878f924239fb29701e8ae149102efe41'
prefix=js(R/'PREFIX_CHECK02.json');assert prefix['status']=='PASS' and [x['batch'] for x in prefix['new_batches']]==list(range(10,16))
absent={str(p):not p.exists() for p in [*[Path('/proc')/str(n) for n in [745583,746180,746711,746724]],Path(guard['cgroup'])]};assert all(absent.values())
print(json.dumps({'status':'PASS','evidence':E,'terminal_reason':failed['reason'],'delivery_note':note,'sampled_peak_bytes':guard['peak_sampled_memory_current_bytes'],'elapsed_seconds':guard['elapsed_seconds'],'sampled_absence':absent,'storage_totals':{k:storage['storage_observation'][k] for k in ['allocated_bytes','logical_file_bytes','entries']},'final_phase_totals':outputs['phase-timing.json'],'group':m,'qualification':'Original FAILED/nulls retained. Bounded local joins, not external recovery, independent numerical agreement, atomic writer exclusion or new admission.'},indent=2))
