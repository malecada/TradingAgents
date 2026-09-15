import importlib.util
import json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_price_ownership',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/source_ownership.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A='0x'+'a'*40;B='0x'+'b'*40;BLOCK='0x'+'c'*64

def key(data,tag=None):return json.dumps(['eth_call',[{'to':m.ORACLE,'data':data},{'blockHash':BLOCK,'requireCanonical':True} if tag is None else tag]])

def test_scalar_failure_excludes_same_asset_in_different_vector():
    scalar='0xb3596f07'+A[2:].rjust(64,'0')
    inventory=m.price_fields([key(scalar)])
    with pytest.raises(ValueError,match='remeasure'):m.assert_new_price_fields(BLOCK,[A,B],inventory)
    m.assert_new_price_fields(BLOCK,[B],inventory)


def test_vector_fields_canonicalized_and_unresolved_tag_never_novel():
    vector='0x9d23d9f2'+format(32,'064x')+format(2,'064x')+A[2:].rjust(64,'0')+B[2:].rjust(64,'0')
    inventory=m.price_fields([key(vector)])
    assert inventory['prior_oracle_fields']==[BLOCK+'|'+A,BLOCK+'|'+B]
    with pytest.raises(ValueError,match='remeasure'):m.assert_new_price_fields(BLOCK,[B.upper()],inventory)
    unresolved=m.price_fields([key(vector,'latest')])
    with pytest.raises(ValueError,match='unresolved'):m.assert_new_price_fields('0x'+'d'*64,[B],unresolved)


def test_noncanonical_prior_oracle_layout_cannot_be_ignored():
    with pytest.raises(ValueError,match='shape'):m.price_fields([key('0xb3596f07'+'0'*62)])
    with pytest.raises(ValueError,match='padding'):m.price_fields([key('0xb3596f07'+'1'*64)])
