"""Strict resource-only selector; uses the genuine matching_owner Binding factory."""
def require(value,message):
    if not value:raise ValueError(message)


def validate_job(value):
    require(type(value) is dict and set(value)=={'schema_version','kind','resources','environment_input','payload'},'resource job fields')
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='compact_resource','explicit resource job kind')
    require(type(value['environment_input']) is str and bool(value['environment_input']),'resource environment input')
    payload=value['payload']
    require(type(payload) is dict and set(payload)=={'representation_jobs'} and type(payload['representation_jobs']) is dict and bool(payload['representation_jobs']),'resource representation selection')


def import_policy(value):
    require(type(value) is dict and set(value)=={'schema_version','max_numeric_bytes','max_stage_bytes'},'import policy fields')
    require(type(value['schema_version']) is int and value['schema_version']==1,'import policy schema')
    require(type(value['max_numeric_bytes']) is int and 0<value['max_numeric_bytes']<=16*1024**2,'import numeric limit')
    require(type(value['max_stage_bytes']) is int and 2*65536<=value['max_stage_bytes']<=4*65536,'import receipt reservation')
    return dict(value)


def open_first(run,*,representation,plan_input,producer,policy_input,job_input):
    from . import matching_owner
    # The actual factory repeats schema, source, runtime, live guard and journal
    # evidence checks. This adapter does not construct a Binding itself.
    return matching_owner.bind(run,representation=representation,plan_input=plan_input,
      producer=producer,policy_input=policy_input,job_input=job_input,_create=True,_first=True,_resource=True)


def assert_selected(bound,job_input):
    record=bound.record;inputs=bound._run.admission.inputs
    require(record.get('resource_only') is True,'genuine resource-only Binding required')
    require(type(job_input) is str and job_input in inputs and record.get('job_input')==job_input,
            'import job input differs from live Binding')
    require(record.get('job_sha256')==inputs[job_input]['sha256'],'import job hash differs from live Binding')
