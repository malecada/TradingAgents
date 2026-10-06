"""Exact candidate-only edits; reads source code, never runtime bodies."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];SRC=ROOT/'tradingagents/research/onchain_replication';OUT=HERE/'candidate'
pins={}
def read(name):
    p=SRC/(name+'.py');b=p.read_bytes();pins[name]={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def sub(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def save(name,s):(OUT/(name+'.py')).write_text(s)

s=read('archive_pair_writer')
s=sub(s,"from . import archive_consume as consume, archived_pair_log as replay","from . import archive_consume as consume, archived_pair_log as replay\nfrom . import archive_read_controls as read_controls")
s=sub(s,"set(value) == {'schema_version', 'remote_prefix',", "set(value)-{'read_controls'} == {'schema_version', 'remote_prefix',")
s=sub(s,"    result = json.loads(io._json(value))", "    result = json.loads(io._json(value))\n    if 'read_controls' in result:read_controls.policy(result['read_controls'])")
save('archive_pair_writer',s)

s=read('archive_owner_policy')
s=sub(s,"from .provenance import freeze, thaw", "from .provenance import freeze, thaw\nfrom . import archive_read_controls as read_controls")
s=sub(s,"'local_free_floor_bytes':policy['local_free_floor_bytes']}\n", "'local_free_floor_bytes':policy['local_free_floor_bytes']} | ({'read_controls':read_controls.policy(policy['read_controls'])} if 'read_controls' in policy else {})\n")
s=sub(s,"set(policy) == FIELDS", "set(policy)-{'read_controls'} == FIELDS")
s=sub(s,"    read_bytes = (3*w['max_chunks']+8)*io.META_LIMIT", "    read_bytes = read_controls.capacity(w['max_chunks'],read_controls.selected(w))['logical_bytes']")
save('archive_owner_policy',s)

s=read('archive_pair_reader')
s=sub(s,"from . import archived_pair_log as replay", "from . import archived_pair_log as replay\nfrom . import archive_read_controls as read_controls")
anchor='\n\nclass _Snapshot:'
helper='''

def _read_metadata_capacity(writer_policy):
    return read_controls.capacity(writer_policy['max_chunks'],read_controls.selected(writer_policy))['logical_bytes']


def _check_read_contents(attempt,source,complete=True):
    fixed={'intent.json'}|({'complete.json'} if complete else set())
    selected=read_controls.selected(source.policy)
    if selected is None:
        _inventory(attempt,fixed,r'chunk-([0-9]{12})',source.count)
        for index in range(source.count):
            mapping,_=source.mapping(index)
            _contents(attempt/writer._chunk(index),_read_bodies(mapping))
    else:
        _inventory(attempt,fixed|{'controls'},r'chunk-([0-9]{12})',0)
        def expected():
            for index in range(source.count):
                mapping,_=source.mapping(index)
                for leaf,raw in _read_bodies(mapping).items():
                    yield read_controls.record_name(index,leaf),raw
        read_controls.audit(attempt,expected(),selected,max_chunks=source.policy['max_chunks'])
'''
s=sub(s,anchor,helper+anchor)
s=sub(s,"(3*source.policy['max_chunks']+8)*io.META_LIMIT <= max_read_metadata_bytes", "_read_metadata_capacity(source.policy) <= max_read_metadata_bytes")
s=sub(s,"            io._write(fd,'intent.json',intent)\n", "            io._write(fd,'intent.json',intent)\n            packed=(read_controls.Writer(attempt,source.policy['max_chunks'],read_controls.selected(source.policy))\n                    if read_controls.selected(source.policy) is not None else None)\n")
s=sub(s,"                return consume.consume(receipt_bytes=io._json(mapping['receipt']),receipt_sha256=mapping['receipt_sha256'],", "                if packed is not None:\n                    return packed.consume(index,receipt_bytes=io._json(mapping['receipt']),receipt_sha256=mapping['receipt_sha256'],\n                        expected_scope=mapping['scope'],transport=transport,lease=live,\n                        free_floor_bytes=source.policy['local_free_floor_bytes'])\n                return consume.consume(receipt_bytes=io._json(mapping['receipt']),receipt_sha256=mapping['receipt_sha256'],")
s=sub(s,"                _inventory(attempt,{'intent.json'}|({'complete.json'} if complete else set()),r'chunk-([0-9]{12})',source.count)","                _check_read_contents(attempt,source,complete)")
s=sub(s,"                for index in range(source.count):\n                    mapping,_ = source.mapping(index)\n                    _contents(attempt/writer._chunk(index),_read_bodies(mapping))\n",'')
save('archive_pair_reader',s)

s=read('archived_stage')
s=sub(s,"(3*source.policy['max_chunks']+8)*io.META_LIMIT <= c['max_read_metadata_bytes']", "reader._read_metadata_capacity(source.policy) <= c['max_read_metadata_bytes']")
s=sub(s,"        reader._inventory(attempt/'events',{'intent.json','complete.json'},r'chunk-([0-9]{12})',source.count)","        reader._check_read_contents(attempt/'events',source)")
s=sub(s,"        for index in range(source.count):\n            mapping,_ = source.mapping(index)\n            reader._contents(attempt/'events'/reader.writer._chunk(index),reader._read_bodies(mapping))\n",'')
save('archived_stage',s)
for name in ('archive_control_history','archive_consume','archive_chunks','score_batches','owned_io'):
    read(name)
(HERE/'SOURCE_PINS01.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
# Accepted scalar metadata adapter: same opt-in changes to reserved bytes/files.
cp=HERE.parent.parent/'real-data-pilot-feature-integration-successor01-2026-10-06/candidate/controls01.py'
# Actual full_sources is three parents above this subdirectory.
cp=HERE.parents[1]/'real-data-pilot-feature-integration-successor01-2026-10-06/candidate/controls01.py'
s=cp.read_text();pins['controls01']={'path':str(cp.relative_to(ROOT)),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest()}
s=sub(s,"'max_workflow_metadata_bytes'},'archive')", "'max_workflow_metadata_bytes'}|({'read_controls'} if 'read_controls' in a else set()),'archive')")
s=sub(s,"    for x in a.values():integer(x)", "    for key,x in a.items():\n        if key!='read_controls':integer(x)")
s=sub(s,"    writer_files=7*Q+8;read_files=3*Q+8", "    writer_files=7*Q+8;read_files=3*Q+8\n    read_bound=read_files*META;read_dirs=Q;archive_max_file=max(META,40*T)\n    if 'read_controls' in a:\n        from tradingagents.research.onchain_replication.archive_read_control_capacity import capacity as read_capacity\n        packed=read_capacity(Q,a['read_controls']);read_bound=packed['logical_bytes'];read_files=packed['files'];read_dirs=packed['directories'];archive_max_file=max(archive_max_file,a['read_controls']['shard_bytes'])")
s=sub(s,"a['max_read_metadata_bytes']>=read_files*META", "a['max_read_metadata_bytes']>=read_bound")
s=sub(s,"archive_dirs=1+ordinary_ops+8*(5+2*Q+R*(5+Q))", "archive_dirs=1+ordinary_ops+8*(5+2*Q+R*(5+read_dirs))")
s=sub(s,"archive_files,archive_dirs,max(META,40*T)", "archive_files,archive_dirs,archive_max_file")
save('controls01',s)
(HERE/'SOURCE_PINS01.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
s=read('archive_dispatch')
s=sub(s,"set(archived)==archive_owner_policy.FIELDS", "set(archived)-{'read_controls'}==archive_owner_policy.FIELDS")
s=sub(s,"        positive=archive_owner_policy.FIELDS-", "        if 'read_controls' in archived:\n            from . import archive_read_controls\n            archive_read_controls.policy(archived['read_controls'])\n        positive=archive_owner_policy.FIELDS-")
save('archive_dispatch',s)
(HERE/'SOURCE_PINS01.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
# Reviewable unified patch; never applies to Main.
import difflib
patch=[]
for p in sorted(OUT.glob('*.py')):
    pin=pins.get(p.stem)
    previous='' if pin is None else (ROOT/pin['path']).read_text()
    target='tradingagents/research/onchain_replication/'+p.name if p.stem!='controls01' else pins['controls01']['path']
    patch.extend(difflib.unified_diff(previous.splitlines(True),p.read_text().splitlines(True),fromfile='/dev/null' if pin is None else 'a/'+target,tofile='b/'+target))
(HERE/'CANDIDATE02.patch').write_text(''.join(patch))
for p in OUT.glob('*.py'):compile(p.read_text(),str(p),'exec')
handoff=HERE.parents[1]/'real-data-pilot-selected-feature-protocol01-2026-10-06/prepare_builder03_input02.py'
s=handoff.read_text();pins['prepare_builder03_input02']={'path':str(handoff.relative_to(ROOT)),'sha256':hashlib.sha256(handoff.read_bytes()).hexdigest()}
s=sub(s,"'max_stage_bytes','max_workflow_metadata_bytes')},", "'max_stage_bytes','max_workflow_metadata_bytes')}|({'read_controls':archive['read_controls']} if 'read_controls' in archive else {}),")
save('prepare_builder03_input02',s)
(HERE/'SOURCE_PINS01.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
patch=[]
for p in sorted(OUT.glob('*.py')):
    pin=pins.get(p.stem);previous='' if pin is None else (ROOT/pin['path']).read_text()
    target=pins[p.stem]['path'] if p.stem in ('controls01','prepare_builder03_input02') else 'tradingagents/research/onchain_replication/'+p.name
    patch.extend(difflib.unified_diff(previous.splitlines(True),p.read_text().splitlines(True),fromfile='/dev/null' if pin is None else 'a/'+target,tofile='b/'+target))
(HERE/'CANDIDATE02.patch').write_text(''.join(patch))
for p in OUT.glob('*.py'):compile(p.read_text(),str(p),'exec')
