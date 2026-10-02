"""Registered archive-policy selection for an existing exact current owner.

This freezes the prospective storage route and conservative logical allowances.
It does not install an archive writer, allocate a read claim, meter transport,
change old owner/stage contracts or admit empirical execution. Those integrations
must consume this explicit selection and enforce its finite allowances.
"""
import json
import re

from . import compact_owner, archive_pair_writer as writer
from .cache import cache_key
from .provenance import freeze, thaw

io = writer.io
require = io._require
BACKEND = 'compact-archive-events-v1'
FIELDS = {'schema_version','backend','transport_identity','remote_namespace',
    'local_free_floor_bytes','max_stage_verifications','max_writer_metadata_bytes',
    'max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes',
    'max_remote_payload_bytes','max_decoded_transfer_bytes'}


def _writer(owner, policy, name):
    limits = thaw(owner.policy['log'])
    count = (limits['max_events']+limits['chunk_events']-1)//limits['chunk_events']
    return {'schema_version':1,'remote_prefix':policy['remote_namespace']+'-'+cache_key({
        'owner':owner.identity,'stage':name}),'transport_identity':policy['transport_identity'],
        'max_chunks':count,'max_metadata_bytes':policy['max_writer_metadata_bytes'],
        'local_free_floor_bytes':policy['local_free_floor_bytes']}


def _inputs(owner, name):
    run = owner.bound._run
    require(type(name) is str and name in run.admission.inputs,'registered archive policy input required')
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][owner.bound.record['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][owner.bound.record['producer']]
    for value in (selected,item):
        require(value.get('native_backend') == owner.policy['backend'],'archive scientific backend selection differs')
        require(value.get('compact_archive_input') == name,'explicit archive policy selection differs')
        require(value['descriptor'].get('compact_archive_execution') == {
            'backend':BACKEND,'policy_sha256':run.admission.inputs[name]['sha256']},
            'archive descriptor policy differs')
        require(cache_key(value['descriptor']) == owner.bound.record['workflow_identity'],
            'archive descriptor differs from bound owner')
    info = run.admission.inputs[name]
    value,reference = compact_owner.matching_owner.metadata(run.admission.root/info['path'],run.admission.root)
    require(reference == info['sha256'],'archive policy registered bytes differ')
    return value,reference


def _record(owner, name, transport):
    require(type(owner) is compact_owner.Owner,'actual current compact owner required')
    owner.boundary();compact_owner.verify_current(owner)
    policy,reference = _inputs(owner,name)
    require(type(policy) is dict and set(policy) == FIELDS and type(policy['schema_version']) is int
        and policy['schema_version'] == 1 and policy['backend'] == BACKEND,'archive owner policy schema')
    positive = FIELDS-{'schema_version','backend','transport_identity','remote_namespace'}
    require(all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in positive),
        'archive owner positive bounded allowances required')
    require(policy['transport_identity'] == writer.archive._transport(transport)
        and type(policy['remote_namespace']) is str
        and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,19}',policy['remote_namespace']),
        'archive endpoint/namespace differs')
    require(policy['max_stage_verifications'] <= 1024,'finite archive verification-count bound')
    stages = tuple(owner.required)
    limits = thaw(owner.policy['log'])
    w = writer._policy(_writer(owner,policy,stages[0]),limits,transport)
    read_bytes = (3*w['max_chunks']+8)*io.META_LIMIT
    references = 40*owner.policy['schedule']['max_total_checkpoints']
    require(policy['max_read_metadata_bytes'] >= read_bytes and policy['max_stage_bytes'] >=
        policy['max_read_metadata_bytes']+references+8*io.META_LIMIT,
        'archive read/reference allowance insufficient')
    count = len(stages);payload = limits['max_events']*writer.events.RECORD_BYTES
    remote = count*payload
    transfer = remote*(3+policy['max_stage_verifications'])
    # Prospective control metadata margin; not a physical allocation bound.
    metadata = 8*io.META_LIMIT+count*(policy['max_writer_metadata_bytes']+8*io.META_LIMIT+
        policy['max_stage_verifications']*policy['max_stage_bytes'])
    require(remote <= policy['max_remote_payload_bytes'] and transfer <= policy['max_decoded_transfer_bytes']
        and metadata <= policy['max_workflow_metadata_bytes'],'archive workflow allowance insufficient')
    result = {'schema_version':1,'backend':BACKEND,'owner':owner.identity,'source_commit':owner.bound.record['source_commit'],
        'policy_input':name,'policy_sha256':reference,'stage_policy_sha256':cache_key(thaw(owner.policy)),
        'required_stages':list(stages),'policy':policy,'capacity':{'stage_count':count,'max_chunks_per_stage':w['max_chunks'],
            'remote_payload_bytes':remote,'decoded_transfer_bytes':transfer,'metadata_bytes':metadata,
            'checkpoint_reference_bytes_per_read':references},'execution_admitted':False}
    owner.boundary();compact_owner.verify_current(owner)
    require(_inputs(owner,name) == (policy,reference) and writer.archive._transport(transport) == policy['transport_identity'],
        'archive selection changed across final owner lease')
    return result


class Selection:
    __slots__ = ('_owner','_input','_transport','_record')
    def __init__(self,owner,name,transport,record):
        object.__setattr__(self,'_owner',owner);object.__setattr__(self,'_input',name)
        object.__setattr__(self,'_transport',transport);object.__setattr__(self,'_record',freeze(record))
    def __setattr__(self,name,value):raise AttributeError('archive selection is immutable')
    record = property(lambda self:self._record)
    def check(self):
        require(_record(self._owner,self._input,self._transport) == thaw(self.record),'archive selection identity changed')
    def writer_policy(self,name):
        self.check()
        require(name in self.record['required_stages'],'archive stage outside registered population')
        return _writer(self._owner,thaw(self.record['policy']),name)


def select(owner, *, input_name, transport):
    require(type(owner) is compact_owner.Owner and not owner.stages and owner.active is None,
        'fresh actual compact owner required before archive selection')
    result = _record(owner,input_name,transport)
    require(not owner.stages and owner.active is None,'fresh compact owner changed during archive selection')
    return Selection(owner,input_name,transport,result)
