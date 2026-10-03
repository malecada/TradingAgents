from pathlib import Path
p=Path(__file__).parent;f=p/'selected_non_tail_transport.py';s=f.read_text().replace("shape=dict(context);shape['slots']", "shape=dict(context);shape['schema_version']=2;shape['slots']");f.write_text(s)
f=p/'completed_f32.py';s=f.read_text();needle="    require(graphs=={s['graph'] for s in policy['slots']},'complete registered raw graph population')\n"
s=s.replace(needle,needle+'''    nodes=selected['descriptor']['resource_fixture']['target_nodes']
    require(set(nodes)==graphs and all(type(n) is int and 1<=n<=4 for n in nodes.values()),'explicit original tiny imported targets; larger populations need separate preparation')
    from . import selected_non_tail_transport as engine
    tx_raw=run.read_input(policy['transport_input']);tx=engine.parse_policy(tx_raw,policy)
    # Full raw container=manifest plus original32-column f32 body. Proposal and
    # actual command budgets remain separate; reserve complete upper bounds.
    parts=commands=rounded=channel=total=0
    for slot in policy['slots']:
        sizes=(8192,4*32*nodes[slot['graph']]);require(slot['max_members']==2 and slot['max_bytes']>=sum(sizes),'complete original raw container reservation insufficient')
        total+=sum(sizes)
        for size in sizes:
            for offset in range(0,size,policy['part_bytes']):
                width=min(policy['part_bytes'],size-offset);parts+=1;commands+=3
                rounded+=engine.charge(0,0,tx['stderr_bytes'],512)+engine.charge(width,0,tx['stderr_bytes'],512)+engine.charge(0,width,tx['stderr_bytes'],512)
                channel+=2*width+3*(tx['stderr_bytes']+2+512)
    require(parts<=policy['max_parts'] and commands<=policy['max_commands'] and rounded<=policy['max_rounded_bytes'],'whole raw proposal bounds')
    require(2*parts<=tx['max_parts'] and commands<=tx['max_commands'] and rounded<=tx['max_rounded_bytes'] and channel<=tx['max_channel_bytes'],'whole raw command/channel bounds')
    require(commands*(tx['command_seconds']+tx['cleanup_seconds'])<=policy['deadline_seconds']<=job['resources']['wall_seconds'],'whole raw command cleanup deadline')
    require(2*total+commands*(tx['stderr_bytes']+2)<=tx['max_local_bytes'] and 3+2*len(nodes)+6*parts<=tx['max_files'],'whole raw recovery/diagnostic local limits')
''');f.write_text(s)
