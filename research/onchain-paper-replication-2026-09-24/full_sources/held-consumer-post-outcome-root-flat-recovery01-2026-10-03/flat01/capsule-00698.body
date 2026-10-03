"""Admitted sampling execution policy; no change to scientific identities."""
import json


def read_sampling_policy(run, input_name):
    if input_name is None:
        return None
    if not isinstance(input_name,str) or not input_name:
        raise ValueError('sampling policy input required')
    value=json.loads(run.read_input(input_name))
    if (not isinstance(value,dict) or set(value)!={'schema_version','mode','max_weight_bytes'}
            or type(value['schema_version']) is not int or value['schema_version']!=1
            or value['mode']!='mapped' or type(value['max_weight_bytes']) is not int
            or value['max_weight_bytes']<=0):
        raise ValueError('sampling storage policy differs')
    return value


def require_sampling_arm(arm, policy):
    if policy is not None and arm not in {'proposed','mcm_without_gat','training_label_permutation'}:
        raise ValueError('sampling policy unused by representation arm')
