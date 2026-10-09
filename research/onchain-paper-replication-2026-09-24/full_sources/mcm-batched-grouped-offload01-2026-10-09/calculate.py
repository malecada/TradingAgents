"""Count-only finite grouping model; optional seven per-graph batch counts."""
import json,sys
B=101559;G=7
counts=json.loads(sys.argv[1]) if len(sys.argv)>1 else None
if counts is not None:
 assert type(counts) is list and len(counts)==G and all(type(n) is int and n>0 for n in counts) and sum(counts)==B
 low=high=sum((n+15)//16 for n in counts)
else:low=(B+15)//16;high=(B+15*G)//16
print(json.dumps({'total_original_batches':B,'group_size_max':16,'groups_min':low,'groups_max':high,'exact_group_count_requires_seven_graph_batch_counts':counts is None,'typed_operations_range':[2*low,2*high],'actual_transport_commands_range':[5*low,5*high],'unchanged_policy_command_reservation_range':[12*low,12*high],'retained_control_files_range':[23*low+G,23*high+G],'work_directory_range':[7*low+3*G,7*high+3*G],'conditional4KiB_control_file_allocation_range':[4096*(23*low+G),4096*(23*high+G)],'original_cells':415968128,'original53byte_payload':415968128*53,'numeric_origins_unchanged':415968128*9,'group_archive_limit':4*1024**2,'group_archive_actual_oversize':'refuse; no truncate/split/retry','payload_or_rss_or_remote_capacity_admitted':False},indent=2))
