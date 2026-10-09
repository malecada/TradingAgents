"""Narrow source-accounting prerequisites only. No Admission or capacity authority."""
import re

def require(value,message):
    if not value:raise ValueError(message)

def check(*,mcm,output,pilot,storage_limits,paths,integer_fields,
          unmodeled_directory_allocated_bytes,other_writer_reserved_bytes,remaining_bytes):
    require(type(mcm) is dict and type(mcm.get('schema_version')) is int and mcm['schema_version']==6,'selected grouped schema6 required')
    b=mcm['batched']
    require(b['retention']=='typed-grouped-recover-before-retire-v1' and type(b['group_batches']) is int and b['group_batches']==16 and type(b['batch_cells']) is int and b['batch_cells']==4096 and type(b['max_body_bytes']) is int and b['max_body_bytes']==1024,'exact accounted batch/body/group required')
    require(type(output.get('schema_version')) is int and output['schema_version']==1 and 'payload_archive_input' not in output,'accounted local f32 publication required')
    require('partial_progress' not in pilot and 'scoring_diagnostic' not in pilot and pilot.get('population_scope')=='resource_pilot_subset','accounted pilot route differs')
    require(storage_limits['max_logical_bytes']==16*1024**3 and storage_limits['max_allocated_bytes']==20*1024**3,'fixed writer caps must not change')
    require(type(paths) in (tuple,list) and bool(paths),'complete actual path roster required')
    for path in paths:
        require(type(path) is str and path.startswith('/') and len(path.encode('ascii'))<=512 and re.fullmatch(r'[A-Za-z0-9_./-]+',path) and all(part not in ('.','..') for part in path.split('/')[1:]),'accounted canonical safe path envelope differs')
    for number in integer_fields:
        require(type(number) is int and 0<=number<2**63,'accounted encoded integer envelope differs')
    for number in (unmodeled_directory_allocated_bytes,other_writer_reserved_bytes,remaining_bytes):
        require(type(number) is int and number>=0,'actual currentness/allocation join missing')
    require(unmodeled_directory_allocated_bytes+other_writer_reserved_bytes<=remaining_bytes,'remaining directory/other-writer room exhausted')
    return {'source_conditions_only':True,'capacity_admitted':False,'sampled_not_quota':True}
