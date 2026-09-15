"""Bounded inherited source-contract inventory. No legacy module execution."""
import argparse
from datetime import datetime, timezone
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from tradingagents.research import ResearchRun

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
FIELDS={'map','by_symbol','symbol','sym','token','pool','version','address','contract','chain','chain_id','quote','token_is_0','token_dec','quote_dec','decimals','month','months','start','end','block','timestamp','ts','source','provider','method','universe','pools','tokens','created_at','creation_block','creation_ts','circulating_supply','total_supply','market_cap','unlock','event_ts','as_of_ts','retrieved_at','observed_at','published_at','availability_basis','schema','schema_version','metadata','manifest','history','failed','delisted','errors','status','date','from_block','to_block','count','rows','path','sha256'}
MARKERS=('event_ts','as_of_ts','retrieved_at','observed_at','published_at','availability_basis','merge_vintages','write_preserving_vintage','require_known_availability','circulating_supply','total_supply','market_cap','unlock','delist','PairCreated','BLOCKS_16D','MONTHS_DEV','full_articles.csv','to_csv','read_csv','to_parquet','read_parquet','universe','get_logs','eth_getLogs','interpol','quote','sell','failed')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def missing(reason):return {'status':'unavailable','reason':reason}

def nofollow_open(path):
    """Walk every component using directory descriptors; never traverse symlinks."""
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('exact absolute path required')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=child
        result=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
    finally:os.close(fd)
    return result


def strict_json(raw):
    def pairs(items):
        obj={}
        for key,value in items:
            if key in obj:raise ValueError('duplicate JSON key')
            obj[key]=value
        return obj
    def constant(value):raise ValueError('nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def shape(value, *, max_nodes=100000, max_depth=32):
    """Aggregate structural field evidence. No token names, numeric data or strings."""
    fields={};dates=set();counts={};nodes=0;unknown=set()
    def walk(item,depth):
        nonlocal nodes
        nodes+=1
        if nodes>max_nodes or depth>max_depth:raise ValueError('structural inspection bound exceeded')
        kind=type(item).__name__;counts[kind]=counts.get(kind,0)+1
        if isinstance(item,dict):
            for key,val in item.items():
                if re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?',key):
                    dates.add(key)
                elif key in FIELDS:
                    fields.setdefault(key,set()).add(type(val).__name__)
                else:
                    unknown.add(hashlib.sha256(key.encode()).hexdigest())
                walk(val,depth+1)
        elif isinstance(item,list):
            for val in item:walk(val,depth+1)
    walk(value,0)
    return {'nodes':nodes,'type_counts':counts,'field_types':{key:sorted(kinds) for key,kinds in sorted(fields.items())},
            'unknown_key_count':len(unknown),'unknown_key_set_sha256':digest(json.dumps(sorted(unknown)).encode()),
            'date_shaped_dictionary_keys':sorted(dates),'interpretation':'structural keys only; dates do not establish vintage or completeness'}


def inspect_metadata(path,cap):
    fd=None;chunks=[];before=after=None;complete=False
    def identity(info):
        return None if info is None else {key:getattr(info,key) for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')}
    def evidence():
        raw=b''.join(chunks)
        return {'path':str(path),'bytes':len(raw),'sha256':digest(raw),'body_complete':complete,
                'digest_scope':'complete stable file' if complete else 'received prefix only',
                'pre_identity':identity(before),'post_identity':identity(after),
                'source_path':str(path),'retrieval_utc':datetime.now(timezone.utc).isoformat(),'retention_limit':'Original file remains untouched; concurrent changes do not preserve the prior version automatically'}
    try:
        fd=nofollow_open(path);before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):raise ValueError('regular file required')
        if before.st_size>cap:raise ValueError('metadata file exceeds frozen4MiB cap; no body read')
        # Never read a cap+1 sentinel: fstat identifies growth without exceeding
        # the total exact8*4MiB reservation, including partial/failed reads.
        remaining=cap
        while remaining:
            block=os.read(fd,min(65536,remaining))
            if not block:break
            chunks.append(block);remaining-=len(block)
        raw=b''.join(chunks);after=os.fstat(fd)
        if identity(before)!=identity(after) or len(raw)!=after.st_size:
            raise ValueError('metadata changed during read or exceeded bound')
        complete=True
        structure=shape(strict_json(raw))
        if len(json.dumps(structure).encode())>120*1024:raise ValueError('sanitized structure exceeds output allowance')
        return {**evidence(),'status':'complete','structure':structure,
                'scope':'metadata structure only, no financial observation or source qualification'}
    except (OSError,ValueError,TypeError,RecursionError) as exc:
        return {**evidence(),**missing(type(exc).__name__+': '+str(exc))}
    finally:
        if fd is not None:os.close(fd)


def inspect_code(raw,path):
    try:
        text=raw.decode('utf-8');tree=ast.parse(text,filename=path)
        return {'status':'complete','path':path,'sha256':digest(raw),'lines':len(text.splitlines()),
                'function_count':sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(tree)),
                'marker_lines':{m:[i for i,line in enumerate(text.splitlines(),1) if m in line] for m in MARKERS if m in text},
                'scope':'text/AST inventory only; marker presence including comments is not implementation or provenance proof'}
    except (UnicodeError,SyntaxError,ValueError) as exc:
        return {'path':path,'sha256':digest(raw),**missing(type(exc).__name__+': '+str(exc))}


def inventory(spec):
    ids=['code-'+str(i) for i in range(len(spec['source_code_inventory']))]
    if spec['experiment'].startswith('defi-depth-q4-'):
        ids += ['metadata-'+str(i) for i in range(len(spec['roots'])*len(spec['fixed_metadata_candidates_relative_to_each_root']))]
    ids += ['requirement-'+str(i) for i in range(len(spec['requirements']))]
    return ids,[x+'.json' for x in ids]+[x+'-attempt.json' for x in ids if x.startswith('metadata-')]+['summary.json']


def inspect(spec,code_inputs,publish,metadata_reader=inspect_metadata):
    rows=[]
    def record(rid,row):
        row={**row,'id':rid}
        if len(json.dumps(row).encode())>128*1024:
            row={'id':rid,'path':row.get('path'),'sha256':row.get('sha256'),**missing('sanitized output exceeds128KiB') }
        rows.append(row);publish(rid+'.json',row)
    for i,path in enumerate(spec['source_code_inventory']):record('code-'+str(i),inspect_code(code_inputs[path],path))
    read=0
    if spec['experiment'].startswith('defi-depth-q4-'):
        targets=[str(Path(root)/rel) for root in spec['roots'] for rel in spec['fixed_metadata_candidates_relative_to_each_root']]
        if len(targets)!=8 or len(set(targets))!=8:raise ValueError('fixed metadata denominator differs')
        for i,path in enumerate(targets):
            publish('metadata-'+str(i)+'-attempt.json',{'path':path,'max_bytes':4*1024*1024,'request_utc':datetime.now(timezone.utc).isoformat(),'scope':'exact preregistered metadata target; no replacement'})
            row=metadata_reader(path,4*1024*1024);read+=row.get('bytes',0);record('metadata-'+str(i),row)
        if read>spec['raw_metadata_cap_bytes']:raise ValueError('metadata byte budget exceeded')
    for i,requirement in enumerate(spec['requirements']):
        record('requirement-'+str(i),{**missing('Bounded metadata/code inspection alone does not establish this causal archive/implementation requirement; independent substantive interpretation required'), 'requirement':requirement})
    if [r['id'] for r in rows]!=inventory(spec)[0]:raise ValueError('cell denominator differs')
    return {'cells':rows,'metadata_bytes_read':read,'network_calls':0,'article_records_read':0,'financial_outcomes':False,
            'strategy_verdict':'none; source-contract inspection cannot reject economic mechanism','elapsed_time_kill':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--question',choices=['q4','q6'],required=True);parser.add_argument('--source',required=True);args=parser.parse_args()
    experiment='defi-depth-'+args.question+'-20260915';registration='research/defi-depth-2026-09-15/gates-'+args.question+'.json'
    with ResearchRun.start(root=ROOT,registration=registration,experiment=experiment,source=args.source) as run:
        gate=json.loads((ROOT/registration).read_text())['experiments'][experiment]
        spec=strict_json(run.read_input('design'));phase=strict_json(run.read_input('phase'))
        if spec['experiment']!=experiment or phase['slots'][args.question.upper()]!={'kind':'source','experiment':experiment} or phase['elapsed_time_kill'] is not False:raise ValueError('phase source grant differs')
        code={path:run.read_input('code_'+str(i)) for i,path in enumerate(spec['source_code_inventory'])}
        for name in gate['inputs']:
            if name not in ('design','phase') and not name.startswith('code_'):run.read_input(name)
        result=inspect(spec,code,run.write_json)
        run.write_json('summary.json',result)
        run.finish([{k:r[k] for k in ('id','status','reason') if k in r} for r in result['cells']])
if __name__=='__main__':main()
