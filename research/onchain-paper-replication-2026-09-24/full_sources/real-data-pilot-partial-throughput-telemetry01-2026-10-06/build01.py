from pathlib import Path
import difflib,hashlib,json
H=Path(__file__).resolve().parent;M=H.parents[3];P=Path('tradingagents/research/onchain_replication');D=H/'candidate'/P;D.mkdir(parents=True)
changes={}
def edit(name,edits):
 original=(M/P/name).read_text();s=original
 for before,after in edits:
  assert s.count(before)==1,(name,before);s=s.replace(before,after)
 (D/name).write_text(s)
 b=H/'baseline'/name;b.parent.mkdir(exist_ok=True);b.write_text(original)
 (H/(name+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='baseline/'+name,tofile='candidate/'+name)))
 changes[name]={'before_sha256':hashlib.sha256(original.encode()).hexdigest(),'after_sha256':hashlib.sha256(s.encode()).hexdigest(),'literal_edits':[{'before':a,'after':b} for a,b in edits]}
edit('compact_mcm.py',[
 ('def produce_imported(execution,graph,*,graph_hash,input_name,output_input):','def produce_imported(execution,graph,*,graph_hash,input_name,output_input,progress=None):\n    if progress is not None:\n        from .real_pilot_partial_progress import MCMProgress\n        require(type(progress) is MCMProgress,\'exact optional pilot telemetry required\')'),
 ('return _produce_locked(target,graph_hash=graph_hash,input_name=input_name,output_input=output_input,held=held)','return _produce_locked(target,graph_hash=graph_hash,input_name=input_name,output_input=output_input,held=held,progress=progress)'),
 ('def _produce_locked(dictionary, *, graph_hash, input_name, output_input, held):','def _produce_locked(dictionary, *, graph_hash, input_name, output_input, held, progress=None):'),
 ('        stage_inode = list(stage.inode)\n','        stage_inode = list(stage.inode)\n        if progress is not None:progress.begin(graph_hash,start[\'rows\'],start[\'motifs\'])\n'),
 ("            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'MCM producer start changed')\n", "            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'MCM producer start changed')\n            if progress is not None:progress.poll(log,stream)\n"),
])
edit('real_pilot_import_caller.py',[
 ("    resource_subset = 'population_scope' in p\n", "    partial = 'partial_progress' in p\n    if partial:\n        from .real_pilot_partial_progress import policy\n        require(full, 'partial progress requires explicit schema2 plan')\n        policy(p['partial_progress'])\n    resource_subset = 'population_scope' in p\n"),
 (" | ({'archive_inputs'} if archive else set()), 'pilot plan fields differ')", " | ({'archive_inputs'} if archive else set()) | ({'partial_progress'} if partial else set()), 'pilot plan fields differ')"),
 ("    terminal = training = None; primary = None\n", "    progress = None\n    if 'partial_progress' in p:\n        from .real_pilot_partial_progress import MCMProgress\n        progress = MCMProgress(p['partial_progress'],{key:len(g.node_ids) for key,g in graphs.items()},\n            claim_sha256=run._claim_sha256,source=run.admission.source)\n    terminal = training = None; primary = None\n"),
 ("result = compact_mcm.produce_imported(execution,g,graph_hash=key,input_name=s['compact_mcm_input'],output_input=s['compact_mcm_output_input'])", "result = compact_mcm.produce_imported(execution,g,graph_hash=key,input_name=s['compact_mcm_input'],output_input=s['compact_mcm_output_input'],\n                **({'progress':progress} if progress is not None else {}))"),
 ("    terminal = terminal or {'schema_version':1,'kind':KIND,'status':'failed','resource_only':True,'reason':row['reason']}\n", "    if progress is not None:summary['partial_mcm_progress'] = progress.summary()\n    terminal = terminal or {'schema_version':1,'kind':KIND,'status':'failed','resource_only':True,'reason':row['reason']}\n")
])
(H/'SOURCE_DELTA01.json').write_text(json.dumps(changes,indent=2)+'\n')
