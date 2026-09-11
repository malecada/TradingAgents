"""Sanitized bounded metadata-region inspection; never reads article records."""
import argparse
import csv
from datetime import datetime, timezone
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat

from tradingagents.research import ResearchRun

REGISTRATION='research/strategy-search-2026-09-11/gates-news-provenance.json'
EXPERIMENT='news-provenance-20260911'
FIELDS=('event_ts','as_of_ts','retrieved_at','source_updated_at','availability_basis','id','url','symbols','source','published_at','created_at','updated_at','date','seendate','content','headline','summary','author')
PLAUSIBLE=('event_ts','as_of_ts','retrieved_at','source_updated_at','id','published_at','created_at','updated_at','date','seendate')
MAX_OUTPUT=4*1024**2


def default_spec():
    base='/home/malecada/master_thesis/'
    targets=[]
    for label,checkout in (('audit','TradingAgents-audit-fixes'),('original','TradingAgents'),('predlab','TradingAgents-predlab')):
        for provider in ('alpaca','gdelt'):
            targets.append({'id':label+'-'+provider,'path':base+checkout+'/data/sentiment/'+provider,'format':'monthly-parquet'})
    targets.append({'id':'external-csv','path':base+'News_fulltext/News_fulltext/full_articles.csv','format':'csv-header'})
    return {'schema_version':1,'experiment':EXPERIMENT,'targets':targets,'field_whitelist':list(FIELDS),
            'plausible_header_fields':list(PLAUSIBLE),'normalization':'strip surrounding whitespace, Unicode casefold; UTF8 BOM allowed',
            'csv_max_bytes':65536,'footer_max_bytes':1048576,'entry_limit':1000,'overflow_iterator_probe':1,
            'footers_per_directory':2,'schema_column_limit':4096,'max_sanitized_receipt_bytes':131072,'max_output_bytes':MAX_OUTPUT,'max_memory_mib':512,'max_cpus':2,'max_wall_seconds':120,
            'parquet_parser':'pyarrow23.0.1 read_schema on isolated PAR1+boundedfooter+length+PAR1; safe primitive type categories only'}


def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()


def _open(path,directory=False):
    """Each absolute component opened relative to a held fd; no symlink race."""
    parts=Path(path).parts
    if not Path(path).is_absolute() or '..' in parts or any(p in ('keys','apis','hf_token.txt') or p.startswith('.env') for p in parts):
        raise PermissionError('forbidden_path')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for i,part in enumerate(parts[1:]):
            flags=os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK
            if i<len(parts)-2 or directory:flags|=os.O_DIRECTORY
            nxt=os.open(part,flags,dir_fd=fd)
            os.close(fd);fd=nxt
        mode=os.fstat(fd).st_mode
        if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
            raise PermissionError('unexpected_file_type')
        return fd
    except BaseException:
        os.close(fd);raise


def _identity(fd):
    value=os.fstat(fd)
    return {'device':value.st_dev,'inode':value.st_ino,'bytes':value.st_size,'mtime_ns':value.st_mtime_ns,'ctime_ns':value.st_ctime_ns,
            'mtime_scope':'Local filesystem attribute only; not historical availability.'}


def _projection(names,types):
    fields={name:{'status':'absent'} for name in FIELDS};unknown=[];seen={}
    for name,kind in zip(names,types,strict=True):
        normalized=name.strip().casefold()
        if normalized in fields:
            seen.setdefault(normalized,[]).append(kind)
        else:unknown.append(digest(name.encode('utf-8')))
    for name,kinds in seen.items():
        fields[name]={'status':'present' if len(kinds)==1 else 'ambiguous','occurrences':len(kinds),'types':sorted(set(kinds))}
    return {'fields':fields,'column_count':len(names),'unknown_column_count':len(unknown),'unknown_name_sha256':unknown,
            'normalization_collisions':sorted(name for name,kinds in seen.items() if len(kinds)>1)}


def _category(value,pa):
    checks=(('null',pa.types.is_null),('boolean',pa.types.is_boolean),('integer',pa.types.is_integer),
            ('floating',pa.types.is_floating),('decimal',pa.types.is_decimal),('string',pa.types.is_string),
            ('large_string',pa.types.is_large_string),('binary',pa.types.is_binary),('large_binary',pa.types.is_large_binary),
            ('timestamp',pa.types.is_timestamp),('date',pa.types.is_date),('time',pa.types.is_time),
            ('duration',pa.types.is_duration),('list',pa.types.is_list),('large_list',pa.types.is_large_list),
            ('struct',pa.types.is_struct),('map',pa.types.is_map),('dictionary',pa.types.is_dictionary))
    return next((label for label,test in checks if test(value)),'unsupported')


def inspect_file(path,format,spec):
    result={'status':'unavailable','regions':[],'historical_availability':'unverified'}
    fd=None
    try:
        fd=_open(path);before=_identity(fd);result['identity_before']=before
        if format=='csv-header':
            raw=bytearray();complete=False
            while len(raw)<spec['csv_max_bytes']:
                value=os.read(fd,1)
                if not value:complete=True;break
                raw.extend(value)
                if value in (b'\n',b'\r'):complete=True;break
            if len(raw)==before['bytes']:complete=True
            result['regions']=[{'offset':0,'length':len(raw),'sha256':digest(raw)}]
            if not complete:raise ValueError('header_limit_or_multiline')
            text=bytes(raw).decode('utf-8-sig',errors='strict')
            records=list(csv.reader(io.StringIO(text,newline=''),strict=True))
            if len(records)!=1 or not records[0]:raise ValueError('invalid_single_line_header')
            if len(records[0])>spec['schema_column_limit']:raise ValueError('schema_column_limit')
            projection=_projection(records[0],['unknown-csv-type']*len(records[0]))
            if not any(projection['fields'][name]['status']!='absent' for name in PLAUSIBLE):
                raise ValueError('header_semantics_unavailable')
        else:
            size=before['bytes']
            if size<12:raise ValueError('invalid_parquet_size')
            magic=os.pread(fd,4,0);tail=os.pread(fd,8,size-8)
            result['regions']=[{'offset':0,'length':len(magic),'sha256':digest(magic)},
                               {'offset':size-8,'length':len(tail),'sha256':digest(tail)}]
            if magic!=b'PAR1' or len(tail)!=8 or tail[4:]!=b'PAR1':raise ValueError('unsupported_parquet_magic')
            length=int.from_bytes(tail[:4],'little')
            if not 0<length<=spec['footer_max_bytes'] or length>size-12:raise ValueError('footer_limit_or_invalid_length')
            offset=size-8-length;footer=os.pread(fd,length,offset)
            result['regions'].append({'offset':offset,'length':len(footer),'sha256':digest(footer)})
            if len(footer)!=length:raise ValueError('footer_short_read')
            import pyarrow as pa
            import pyarrow.parquet as pq
            if pa.__version__!='23.0.1':raise ValueError('unsupported_parser_version')
            schema=pq.read_schema(pa.BufferReader(b'PAR1'+footer+tail))
            if len(schema)>spec['schema_column_limit']:raise ValueError('schema_column_limit')
            projection=_projection(schema.names,[_category(field.type,pa) for field in schema])
        result.update(status='present',schema=projection)
    except MemoryError:raise
    except Exception as exc:
        # Never publish parser messages: they can contain header names or values.
        result['reason_code']='missing' if isinstance(exc,FileNotFoundError) else ('forbidden_or_nonregular' if isinstance(exc,PermissionError) or isinstance(exc,OSError) and exc.errno in (errno.ELOOP,errno.ENOTDIR) else 'unsupported_or_invalid_metadata')
    finally:
        if fd is not None:
            try:
                after=_identity(fd);result['identity_after']=after
                other=_open(path)
                try:result['path_identity_after']=_identity(other)
                finally:os.close(other)
                if result.get('identity_before')!=after or after!=result['path_identity_after']:result.update(status='unavailable',reason_code='concurrent_file_change');result.pop('schema',None)
            except OSError:
                result.update(status='unavailable',reason_code='concurrent_path_change');result.pop('schema',None)
            finally:os.close(fd)
    return result


def inventory_directory(path,spec):
    candidates=[];count=0;overflow=False;rootfd=None
    try:
        rootfd=_open(path,True)
        def entries(fd):
            nonlocal count,overflow
            with os.scandir(fd) as stream:
                for entry in stream:
                    if count==spec['entry_limit']:
                        overflow=True;return
                    count+=1
                    yield entry
        years=[]
        for entry in entries(rootfd):
            if re.fullmatch(r'[0-9]{4}',entry.name):years.append(entry.name)
        for year in sorted(years):
            if overflow:break
            yearfd=None
            try:
                yearfd=os.open(year,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
                for entry in entries(yearfd):
                    if re.fullmatch(r'(0[1-9]|1[0-2])\.parquet',entry.name):candidates.append(year+'/'+entry.name)
            except OSError:
                # A year-like forbidden/unreadable path makes inventory incomplete.
                return {'status':'unavailable','reason_code':'year_path_unavailable','processed_entries':count,'overflow_probe':overflow},[]
            finally:
                if yearfd is not None:os.close(yearfd)
        if overflow:return {'status':'partial','reason_code':'entry_limit','processed_entries':count,'overflow_probe':True},[]
        return {'status':'complete','processed_entries':count,'overflow_probe':False,'eligible_month_count':len(candidates)},sorted(candidates)[:2]
    except MemoryError:raise
    except Exception as exc:
        return {'status':'missing' if isinstance(exc,FileNotFoundError) else 'unavailable','reason_code':'target_missing_or_forbidden','processed_entries':count,'overflow_probe':overflow},[]
    finally:
        if rootfd is not None:os.close(rootfd)


def inspect(spec,persist_receipt=None):
    if encoded(spec)!=encoded(default_spec()):raise ValueError('news provenance specification differs from frozen policy/targets')
    receipts=[];subslots=[];cells=[]
    for target in spec['targets']:
        identity=target['id'];receipt={'id':identity,'format':target['format'],'observation_utc':datetime.now(timezone.utc).isoformat(),'historical_availability':'unverified'}
        slots=[]
        if target['format']=='csv-header':
            result=inspect_file(target['path'],'csv-header',spec)
            receipt['inventory']={'status':'missing' if result.get('reason_code')=='missing' else ('complete' if 'identity_before' in result else 'unavailable')}
            slots=[{'id':identity+'-header',**result}]
        else:
            inventory,selected=inventory_directory(target['path'],spec);receipt['inventory']=inventory
            for index in range(2):
                result=({'relative_month':selected[index],**inspect_file(target['path']+'/'+selected[index],'parquet',spec)} if index<len(selected)
                        else {'status':'unavailable','reason_code':'no_fixed_selection','historical_availability':'unverified'})
                slots.append({'id':identity+'-footer-'+str(index+1),**result})
        selected=[slot for slot in slots if slot.get('reason_code')!='no_fixed_selection']
        receipt['schema_slots']=slots
        if len(encoded(receipt))>spec['max_sanitized_receipt_bytes']-1024:
            for slot in slots:
                slot.pop('schema',None);slot.update(status='unavailable',reason_code='sanitized_projection_budget')
        receipt['status']='complete' if receipt['inventory']['status']=='complete' and selected and all(slot['status']=='present' for slot in selected) else 'unavailable'
        if receipt['status']=='unavailable':receipt['reason']='bounded schema source unavailable; see separate inventory/schema dimensions'
        receipts.append(receipt);subslots.extend(slots)
        cells.append({'id':identity,'status':receipt['status'],**({'reason':receipt['reason']} if receipt['status']=='unavailable' else {})})
        if persist_receipt is not None:persist_receipt(identity+'-receipt.json',receipt)
    inventory={'schema_version':1,'sources':receipts,'subslots':subslots,'source_count':7,'schema_slot_count':13}
    admission={'schema_version':1,'cells':cells,'schema_slots':[{key:slot[key] for key in ('id','status')} for slot in subslots],
               'historical_availability':'unverified; field presence does not establish first observation, revisions, corpus identity or causal availability'}
    if sum(len(encoded(row)) for row in receipts)+len(encoded(inventory))+len(encoded(admission))>MAX_OUTPUT:
        raise ValueError('sanitized output exceeds4MiB; previously persisted receipts retained')
    return inventory,admission,cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        inventory,admission,cells=inspect(json.loads(run.read_input('request_spec')),run.write_json)
        run.write_json('inventory.json',inventory);run.write_json('admission.json',admission);run.finish(cells)


if __name__=='__main__':main()
