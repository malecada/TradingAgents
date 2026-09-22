"""Offline material routing; preserved capture formats and physical numbering."""
import importlib.util
import json
from pathlib import Path
import struct
import urllib.parse

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fullpanel_retained_adapter',HERE.parent/'pilot2/day.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
old=adapter.old
numeric=old.numeric
storage=old.storage

def material(root,plan,date,boundary=False):
    root=Path(root)
    if date=='2024-01-01':
        result=adapter.retained_context(root,plan,date)
        return (None,None,result[2],None) if boundary else result
    descriptor=plan['captures'][date]
    if 'reused_blocks' not in descriptor:return adapter.retained_capture(root,plan,date,boundary=boundary)
    # January 9's historical selected capture has tail/footer/ranges numbered
    # from one; its block response belongs to the preserved earlier capture.
    reused=dict(plan,captures={**plan['captures'],date:descriptor['reused_blocks']})
    blocks=adapter.retained_capture(root,reused,date,boundary=True)[2]
    if boundary:return None,None,blocks,None
    directory=Path(descriptor['directory']).resolve()
    manifest=json.loads(adapter.verified(root,descriptor['manifest']))
    state=manifest.get('result',manifest)
    if state['status']!='complete' or state['date']!=date:raise ValueError('unavailable retained capture')
    members={}
    for item in manifest['files']:
        if item['path'] in members:raise ValueError('duplicate capture member')
        adapter.verified(directory,item);members[item['path']]=item
    def member(name):return adapter.verified(directory,members[name])
    inventory=json.loads(adapter.verified(root,plan['inputs'][plan['inventory_input']]))
    obj=old.object_for(inventory,'transactions',date)
    def read(number,first,last):
        stem=f'request-{number:04d}';receipt=json.loads(member(stem+'.json'));intent=json.loads(member(stem+'-intent.json'))
        headers={'If-Match':obj['etag'],'Range':f'bytes={first}-{last}'};url=plan['base_url']+urllib.parse.quote(obj['key'],safe='/=')
        if any(r['request_number']!=number or r['url']!=url or r['request_headers']!=headers for r in [receipt,intent]):raise ValueError('retained transaction request identity differs')
        blob=receipt['blob']
        if blob['path']!=stem+'.body.zst':raise ValueError('unexpected blob path')
        member(blob['path']);raw=storage.read_blob(adapter.within(directory,blob['path']),blob)
        if len(raw)!=receipt['bytes'] or storage.sha(raw)!=receipt['sha256']:raise ValueError('raw response digest differs')
        return old.checked_response(raw,receipt,obj,first,last)
    tail=read(1,obj['size']-8,obj['size']-1);length=struct.unpack('<I',tail[:4])[0]
    if tail[4:]!=b'PAR1' or not 0<length<=plan['limits']['max_footer_bytes'] or length+12>obj['size']:raise ValueError('invalid footer')
    footer=read(2,obj['size']-length-8,obj['size']-1)
    if footer[-8:]!=tail:raise ValueError('footer mismatch')
    projection=numeric.projection(obj,footer,plan['limits'],plan['required_types'])
    if json.loads(member('projection.json'))!=projection:raise ValueError('projection mismatch')
    receipts={n for n in members if n.startswith('request-') and n.endswith('.json') and not n.endswith('-intent.json')}
    if receipts!={f'request-{i:04d}.json' for i in range(1,len(projection['ranges'])+3)}:raise ValueError('request denominator differs')
    def read_range(index):
        span=projection['ranges'][index];return read(index+3,span['start'],span['end'])
    return projection,footer,blocks,read_range
