"""Synthetic retained transport formats; no historical bodies are opened."""
import importlib.util
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
source=module('fullpanel_source_test',ROOT/'research/onchain-graph-2026-09-16/fullpanel/source.py')
fixture=module('fullpanel_capture_fixture',ROOT/'tests/research/test_onchain_pilot2_day.py')
def composite(tmp):
 plan=fixture.capture(tmp);date='2024-01-09';original=tmp/'capture';manifest=json.loads((tmp/'manifest.json').read_bytes());inventory=json.loads((tmp/'inventory.json').read_bytes())
 for x in inventory['inventories'][0]['dates']:x['date']=date
 raw=json.dumps(inventory).encode();(tmp/'inventory.json').write_bytes(raw);plan['inputs']['inventory']['sha256']=source.storage.sha(raw)
 blocks=dict(status='complete',date=date,files=[m for m in manifest['files'] if m['path'].startswith('request-0001')]);raw=json.dumps(blocks).encode();(tmp/'blocks.json').write_bytes(raw)
 new=tmp/'selected';new.mkdir();(new/'projection.json').write_bytes((original/'projection.json').read_bytes())
 receipts=sorted(p for p in original.glob('request-*.json') if not p.name.endswith('-intent.json'))
 for n,p in enumerate(receipts[1:],1):
  oldstem=p.stem;stem=f'request-{n:04d}'
  for suffix in ['.json','-intent.json']:
   x=json.loads((original/(oldstem+suffix)).read_bytes());x['request_number']=n
   if 'blob' in x:x['blob']['path']=stem+'.body.zst'
   (new/(stem+suffix)).write_text(json.dumps(x))
  (new/(stem+'.body.zst')).write_bytes((original/(oldstem+'.body.zst')).read_bytes())
 raw=json.dumps(dict(status='complete',date=date,files=source.old.artifact_manifest(new,new))).encode();(tmp/'selected.json').write_bytes(raw)
 plan['captures']={date:dict(directory=str(new),manifest=dict(path='selected.json',sha256=source.storage.sha(raw)),reused_blocks=dict(directory=str(original),manifest=dict(path='blocks.json',sha256=source.storage.sha((tmp/'blocks.json').read_bytes()))))}
 return plan

def test_reused_blocks_keep_physical_request_numbers(tmp_path):
 plan=composite(tmp_path);projected,footer,blocks,read=source.material(tmp_path,plan,'2024-01-09')
 assert projected['rows']==7 and blocks
 assert all(len(read(i))==r['bytes'] for i,r in enumerate(projected['ranges']))
 assert source.material(tmp_path,plan,'2024-01-09',boundary=True)==(None,None,blocks,None)

@pytest.mark.parametrize('target',['blocks.json','selected.json','selected/request-0001.body.zst'])
def test_composite_corruption_is_rejected(tmp_path,target):
 plan=composite(tmp_path);p=tmp_path/target;p.write_bytes(p.read_bytes()+b'x')
 with pytest.raises((ValueError,AssertionError)):source.material(tmp_path,plan,'2024-01-09')
