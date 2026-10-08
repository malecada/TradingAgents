"""Independent authentication boundaries around the newly lowered startup tuple."""
import copy,dataclasses,importlib.util
from pathlib import Path
import pytest
H=Path(__file__).resolve().parent;C=H.parent.parent/'real-data-pilot-startup-reserve-correction01-2026-10-08'
spec=importlib.util.spec_from_file_location('reviewed_startup_fixtures',C/'test_startup01.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
registered=fixtures.registered;context=fixtures.context;live=fixtures.live
from tradingagents.research.onchain_replication import job,resources,real_pilot_import_caller as caller
G=1024**3

@pytest.mark.parametrize('mutation',['owner_source','owner_identity','startup_mismatch','reserve_mismatch','swap'])
def test_live_authenticated_tuple_equality(context,live,mutation):
 ad,e=context;value=live[1]
 if mutation=='owner_source':value['owner_identity']['source_commit']='f'*40
 elif mutation=='owner_identity':value['owner_identity']['experiment']='different-fixed-identity'
 elif mutation=='startup_mismatch':value['start_reserve_bytes']=17*G//2 if e['resources']['start_reserve_bytes']==5*G//2 else 5*G//2
 elif mutation=='reserve_mismatch':value['reserve_bytes']+=1
 else:value['memory_swap_max_bytes']=1
 with pytest.raises(RuntimeError,match='authenticated pilot reserve differs'):fixtures.check_live(context,live)

def test_nonready_admission_cannot_authorize_amendment(context):
 ad,e=context;ad=dataclasses.replace(ad,ready=False)
 with pytest.raises(ValueError,match='authenticated execution job required'):job.resource_policy(e['resources'],ad.root,pilot_context=(ad,e))

@pytest.mark.parametrize('field,value',[('memory_max_bytes',5*G),('memory_high_bytes',4*G),('disk_floor_bytes',11*G)])
def test_no_neighboring_resource_tuple_bypass(context,field,value):
 ad,e=context;e=copy.deepcopy(e);e['resources'][field]=value
 assert not caller._amended_host_reserve(e['resources'])
 with pytest.raises(ValueError,match='host reserves below contract'):job.resource_policy(e['resources'],ad.root,pilot_context=(ad,e))
