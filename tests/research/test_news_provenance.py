"""Synthetic path/header/footer fixtures only; no actual corpus targets opened."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

DIRECTORY=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
loader=importlib.util.spec_from_file_location('news_test_inspector',DIRECTORY/'news_provenance.py')
engine=importlib.util.module_from_spec(loader);loader.loader.exec_module(engine)


def parquet(path):
    schema=pa.schema([pa.field('id',pa.int64()),pa.field('retrieved_at',pa.timestamp('ns')),pa.field('headline',pa.string()),pa.field('private-name',pa.string())],metadata={b'private-meta':b'NEVER-EMIT-CONTENT'})
    out=pa.BufferOutputStream();pq.write_table(pa.Table.from_batches([],schema=schema),out)
    raw=out.getvalue().to_pybytes();length=int.from_bytes(raw[-8:-4],'little');footer=raw[-8-length:-8]
    # Simulated data region must never be read by inspection.
    body=b'PAR1'+b'FORBIDDEN-DATA-PAGES'*37+footer+length.to_bytes(4,'little')+b'PAR1'
    path.write_bytes(body)
    return len(body)-8-length,length


def test_parquet_reads_only_metadata_regions_and_sanitizes(tmp_path,monkeypatch):
    path=tmp_path/'fixture.parquet';offset,length=parquet(path);reads=[]
    actual=engine.os.pread
    def pread(fd,size,where):reads.append((size,where));return actual(fd,size,where)
    monkeypatch.setattr(engine.os,'pread',pread)
    result=engine.inspect_file(str(path),'parquet',engine.default_spec())
    assert result['status']=='present',result
    assert reads==[(4,0),(8,path.stat().st_size-8),(length,offset)]
    assert result['schema']['fields']['id']['types']==['integer']
    encoded=engine.encoded(result)
    assert b'NEVER-EMIT-CONTENT' not in encoded and b'private-name' not in encoded and b'FORBIDDEN-DATA' not in encoded
    assert result['schema']['unknown_name_sha256']==[hashlib.sha256(b'private-name').hexdigest()]


def test_csv_first_physical_line_no_readahead_unknown_names_hash(tmp_path,monkeypatch):
    path=tmp_path/'sample.csv';header=b'ID,retrieved_at,headline,secret-name\n'
    path.write_bytes(header+b'SECRET-RECORD-BODY\n');calls=[];actual=engine.os.read
    def read(fd,size):calls.append(size);return actual(fd,size)
    monkeypatch.setattr(engine.os,'read',read)
    result=engine.inspect_file(str(path),'csv-header',engine.default_spec())
    assert result['status']=='present' and calls==[1]*len(header)
    assert result['regions'][0]['length']==len(header)
    assert b'SECRET' not in engine.encoded(result) and b'secret-name' not in engine.encoded(result)


@pytest.mark.parametrize('raw',[b'This is an article,private content\nnext\n',b'id,"multi\nline"\n',b'id,\xff\n',b'id,'+b'x'*65536,b'"id" broken,foo\n'])
def test_invalid_headerless_multiline_oversized_never_emits_text(tmp_path,raw):
    path=tmp_path/'sample.csv';path.write_bytes(raw)
    result=engine.inspect_file(str(path),'csv-header',engine.default_spec())
    assert result['status']=='unavailable'
    assert 'schema' not in result and result['regions'][0]['length']<=65536


def test_header_normalization_collision_retained(tmp_path):
    path=tmp_path/'sample.csv';path.write_bytes(b'id, ID ,date\n')
    result=engine.inspect_file(str(path),'csv-header',engine.default_spec())
    assert result['schema']['fields']['id']['status']=='ambiguous'


@pytest.mark.parametrize('intermediate',[False,True])
def test_symlinks_in_any_component_rejected(tmp_path,intermediate):
    directory=tmp_path/'real';directory.mkdir();(directory/'header.csv').write_bytes(b'id,date\n')
    link=tmp_path/'link';link.symlink_to(directory if intermediate else directory/'header.csv')
    target=link/'header.csv' if intermediate else link
    result=engine.inspect_file(str(target),'csv-header',engine.default_spec())
    assert result['status']=='unavailable' and not result['regions']


def test_footer_cap_and_unsupported_magic_never_read_pages(tmp_path,monkeypatch):
    path=tmp_path/'bad.parquet';path.write_bytes(b'PAR1'+b'x'*16+(1048577).to_bytes(4,'little')+b'PAR1')
    reads=[];actual=engine.os.pread
    monkeypatch.setattr(engine.os,'pread',lambda fd,size,offset:(reads.append((size,offset)),actual(fd,size,offset))[1])
    assert engine.inspect_file(str(path),'parquet',engine.default_spec())['status']=='unavailable'
    assert len(reads)==2


def test_exact_entry_cap_and_overflow_no_schema_substitute(tmp_path):
    directory=tmp_path/'root';directory.mkdir()
    for i in range(1000):(directory/f'excluded-{i}').touch()
    info,selected=engine.inventory_directory(str(directory),engine.default_spec())
    assert info['status']=='complete' and info['processed_entries']==1000 and not selected
    (directory/'one-more').touch()
    info,selected=engine.inventory_directory(str(directory),engine.default_spec())
    assert info['status']=='partial' and info['processed_entries']==1000 and info['overflow_probe'] is True and not selected


def test_first_two_lexical_include_failed_file_without_substitute(tmp_path):
    directory=tmp_path/'root';(directory/'2025').mkdir(parents=True)
    for name in ('03','01','02'):(directory/'2025'/f'{name}.parquet').write_bytes(b'bad')
    info,selected=engine.inventory_directory(str(directory),engine.default_spec())
    assert info['status']=='complete' and selected==['2025/01.parquet','2025/02.parquet']


def test_concurrent_file_change_or_path_swap_removes_schema(tmp_path,monkeypatch):
    path=tmp_path/'sample.csv';path.write_bytes(b'id,date\n')
    real=engine._identity;counter=0
    def identity(fd):
        nonlocal counter
        counter+=1
        result=real(fd)
        if counter==2:result['bytes']+=1
        return result
    monkeypatch.setattr(engine,'_identity',identity)
    result=engine.inspect_file(str(path),'csv-header',engine.default_spec())
    assert result['status']=='unavailable' and 'schema' not in result


def test_inplace_rewrite_with_restored_mtime_is_unavailable(tmp_path,monkeypatch):
    path=tmp_path/'sample.csv';path.write_bytes(b'id,date\n')
    before=path.stat();actual=engine.os.read;changed=False
    # Allow the filesystem ctime clock to advance; sub-tick changes are not
    # guaranteed observable through filesystem metadata alone.
    import time
    time.sleep(.02)
    def read(fd,size):
        nonlocal changed
        value=actual(fd,size)
        if value==b'\n' and not changed:
            changed=True
            path.write_bytes(b'id,time\n')
            os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
        return value
    monkeypatch.setattr(engine.os,'read',read)
    result=engine.inspect_file(str(path),'csv-header',engine.default_spec())
    assert changed and path.stat().st_mtime_ns==before.st_mtime_ns
    assert result['status']=='unavailable' and 'schema' not in result
    assert result['reason_code']=='concurrent_file_change'


def synthetic_spec(tmp_path):
    spec=engine.default_spec()
    for target in spec['targets']:
        target['path']=str(tmp_path/target['id'])
        if target['format']=='csv-header':Path(target['path']).write_bytes(b'id,retrieved_at,headline\nSECRET-RECORD\n')
        else:
            directory=Path(target['path'])/'2025';directory.mkdir(parents=True)
            parquet(directory/'01.parquet');parquet(directory/'02.parquet')
    return spec


def test_all_seven_and_thirteen_retained_with_sanitized_receipts(tmp_path,monkeypatch):
    spec=synthetic_spec(tmp_path);monkeypatch.setattr(engine,'default_spec',lambda:spec)
    receipts=[];inventory,admission,cells=engine.inspect(spec,lambda name,row:receipts.append((name,row)))
    assert len(cells)==len(receipts)==7 and len(inventory['subslots'])==len(admission['schema_slots'])==13
    assert all(cell['status']=='complete' for cell in cells)
    assert sum(len(engine.encoded(row)) for _,row in receipts)+len(engine.encoded(inventory))+len(engine.encoded(admission))<=4*1024**2
    assert b'SECRET-RECORD' not in engine.encoded(inventory)


def test_missing_roots_still_keep_full_denominators(tmp_path,monkeypatch):
    spec=engine.default_spec()
    for target in spec['targets']:target['path']=str(tmp_path/target['id'])
    monkeypatch.setattr(engine,'default_spec',lambda:spec)
    inventory,_,cells=engine.inspect(spec)
    assert len(cells)==7 and len(inventory['subslots'])==13
    assert all(cell['status']=='unavailable' for cell in cells)
    assert all(source['inventory']['status']=='missing' for source in inventory['sources'])


def test_projection_budget_and_column_count_keep_denominator(tmp_path,monkeypatch):
    spec=synthetic_spec(tmp_path)
    csvpath=Path(spec['targets'][-1]['path'])
    csvpath.write_text('id,'+','.join(['x']*4000)+'\n')
    monkeypatch.setattr(engine,'default_spec',lambda:spec)
    receipts=[];inventory,_,cells=engine.inspect(spec,lambda name,row:receipts.append(row))
    slot=inventory['subslots'][-1]
    assert slot['status']=='unavailable' and slot['reason_code']=='sanitized_projection_budget' and 'schema' not in slot
    assert slot['regions'] and len(receipts)==len(cells)==7
    assert all(len(engine.encoded(row))<=131072 for row in receipts)
    csvpath.write_text('id,'+','.join(['x']*4096)+'\n')
    assert engine.inspect_file(str(csvpath),'csv-header',spec)['status']=='unavailable'


def test_corrupt_footer_is_sanitized_not_parser_error_text(tmp_path):
    path=tmp_path/'bad.parquet';footer=b'PRIVATE-ARTICLE-STRING-THRIFT-INVALID'
    path.write_bytes(b'PAR1'+footer+len(footer).to_bytes(4,'little')+b'PAR1')
    result=engine.inspect_file(str(path),'parquet',engine.default_spec())
    assert result['status']=='unavailable' and len(result['regions'])==3
    assert b'PRIVATE-ARTICLE' not in engine.encoded(result)


DRIVER=r'''
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
loader=importlib.util.spec_from_file_location('synthetic_fixture',root/'tests/research/test_news_provenance.py')
fixture=importlib.util.module_from_spec(loader);loader.loader.exec_module(fixture)
# Only synthetic paths substitute the fixed production target map; parser/I/O/CLI unchanged.
spec=fixture.synthetic_spec(root/'invented-corpus')
fixture.engine.default_spec=lambda:spec
(root/'request-spec.json').write_text(json.dumps(spec))
from tradingagents.research import runtime_hashes
from tradingagents.research.verify import verify_run
sourcepath='research/strategy-search-2026-09-11/news_provenance.py'
def sha(path):return hashlib.sha256((root/path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
git('init','-q')
(root/'charter.md').write_text('Synthetic sanitized schema inspection only. No real corpus.')
exp={'family':'synthetic','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'invented schema lifecycle',
     'stage':'development','reuse':'exploratory','windows':[{'dataset':'synthetic','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],
     'inputs':{'request_spec':{'path':'request-spec.json','sha256':sha('request-spec.json'),'dataset':'synthetic'}},
     'source_files':{name:sha(name) for name in (sourcepath,'driver.py','tests/research/test_news_provenance.py')},'runtime_hashes':runtime_hashes(),'selection':None,
     'cells':[target['id'] for target in spec['targets']],'outputs':[target['id']+'-receipt.json' for target in spec['targets']]+['inventory.json','admission.json']}
gate={'schema_version':1,'program_id':'invented-news','families':{'synthetic':{'mechanism_id':'invented-news','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},
      'datasets':{'synthetic':{'identity':'invented-news','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},
      'experiments':{'news-provenance-20260911':exp}}
(root/'research/strategy-search-2026-09-11/gates-news-provenance.json').write_text(json.dumps(gate))
git('add','.')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic metadata-only lifecycle')
source=git('rev-parse','HEAD');sys.argv=['news_provenance.py','--source',source]
fixture.engine.main()
directory=root/'research_runs/news-provenance-20260911'
verified=verify_run(directory)
inventory=json.loads((directory/'outputs/inventory.json').read_text())
actual=sum(path.stat().st_size for path in (directory/'outputs').iterdir())
assert verified['cell_count']==7 and verified['unavailable_count']==0 and verified['output_count']==9
assert len(inventory['subslots'])==13 and actual<=4*1024**2
assert b'SECRET-RECORD' not in (directory/'outputs/inventory.json').read_bytes()
(root/'synthetic-result.json').write_text(json.dumps({'verification':verified,'subslots':13,'output_bytes':actual,'cpus':len(os.sched_getaffinity(0)),
    'inspector_sha256':sha(sourcepath),'spec_sha256':sha('request-spec.json'),'scope':'Only default_spec target paths replaced by invented temporary corpus paths; real inspector I/O/projection and CLI/lifecycle unchanged.'}))
'''


def test_guarded_actual_cli_on_only_synthetic_paths(tmp_path):
    import shutil
    loader=importlib.util.spec_from_file_location('news_guard',DIRECTORY/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(loader);loader.loader.exec_module(guard)
    program=tmp_path/'research/strategy-search-2026-09-11';program.mkdir(parents=True)
    shutil.copyfile(DIRECTORY/'news_provenance.py',program/'news_provenance.py')
    root=DIRECTORY.parents[1]
    package=tmp_path/'tradingagents';package.mkdir()
    shutil.copyfile(root/'tradingagents/__init__.py',package/'__init__.py')
    shutil.copytree(root/'tradingagents/research',package/'research',ignore=shutil.ignore_patterns('__pycache__'))
    tests=tmp_path/'tests/research';tests.mkdir(parents=True)
    shutil.copyfile(Path(__file__),tests/'test_news_provenance.py')
    (tmp_path/'driver.py').write_text(DRIVER)
    report=guard.run_guard([sys.executable,'-B',str(tmp_path/'driver.py')])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['subslots']==13 and result['cpus']<=2
