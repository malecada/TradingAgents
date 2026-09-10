"""Receipt integrity and conditional index-data envelopes; no portfolio calculation."""
from pathlib import Path
from decimal import Decimal
import csv, datetime, hashlib, io, json, zipfile
p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
zpath=p/'vision-bnx-index-20250317-zip.bin'
expected=(p/'vision-bnx-index-20250317-checksum.bin').read_text().split()[0]
assert sha(zpath)==expected
with zipfile.ZipFile(zpath) as z:
 assert z.namelist()==['BNXUSDT-1m-2025-03-17.csv']
 raw=z.read(z.namelist()[0])
 rows=list(csv.reader(io.StringIO(raw.decode())))
 header=rows.pop(0)
arc={int(r[0]):r for r in rows}
assert len(arc)==len(rows)
start,end=1742200200000,1742202000000
api=json.loads((p/'index-final-window-api.bin').read_text())
assert len(api)==31 and [r[0] for r in api]==list(range(start,end+60000,60000))
assert all(all(Decimal(str(a))==Decimal(b) for a,b in zip(row,arc[row[0]])) for row in api)
window=[arc[t] for t in range(start,end,60000)]
assert len(window)==30
assert all(int(r[6])==int(r[0])+59999 for r in window)
assert all(Decimal(r[3])<=min(Decimal(r[1]),Decimal(r[4]))<=max(Decimal(r[1]),Decimal(r[4]))<=Decimal(r[2]) for r in window)
count=sum(int(r[8]) for r in window)
weightedlo=sum(Decimal(r[3])*int(r[8]) for r in window)
weightedhi=sum(Decimal(r[2])*int(r[8]) for r in window)
iso=lambda t:datetime.datetime.fromtimestamp(t/1000,datetime.timezone.utc).isoformat()
summary={'kind':'price_data_integrity_only','source_sha256':{f.name:sha(f) for f in [zpath,p/'vision-bnx-index-20250317-checksum.bin',p/'index-final-window-api.bin']},'zip_checksum_matches':True,'zip_member_sha256':hashlib.sha256(raw).hexdigest(),'zip_csv_header':header,'archive_rows':len(rows),'archive_min_open_utc':iso(min(arc)),'archive_max_open_utc':iso(max(arc)),'api_archive_all_12_fields_equal_for_31_rows':True,'window_start_inclusive_utc':iso(start),'window_end_exclusive_utc':iso(end),'minute_rows_expected':30,'minute_rows_observed':30,'index_basic_data_count':count,'generic_rule_one_second_count':1800,'non60_rows':[{'open_utc':iso(int(r[0])),'count':int(r[8])} for r in window if int(r[8])!=60],'count_semantics':'Vision header=count; archived official API labels field[8] Number of bisic data (sic). Exact timestamp, missing-update and fill semantics are not supplied.','observed_sample_mean_interval_conditional':{'low':str(weightedlo/Decimal(count)),'high':str(weightedhi/Decimal(count)),'formula':'sum(count_i * low_i)/sum(count_i) <= observed-sample mean <= sum(count_i * high_i)/sum(count_i)','assumptions':'Each count_i is the number of relevant observations represented by its reported OHLC extrema; reported decimal extrema enclose those observations. This bounds the represented 1798-sample mean only, not the 1800-sample contractual settlement mean.'},'equal_60_samples_per_minute_interval_conditional':{'low':str(sum(Decimal(r[3]) for r in window)/Decimal(30)),'high':str(sum(Decimal(r[2]) for r in window)/Decimal(30)),'formula':'mean(minute lows) <= mean(1800 equally sampled index values) <= mean(minute highs)','assumptions':'Requires all60 relevant one-second values in every minute to be within reported extrema, same settlement index, [08:30,09:00) endpoint convention, and no unaccounted rounding. Two counts59 leave this completeness assumption unestablished.'},'exact_settlement_price_identified':False,'unconditional_actual_settlement_bound_identified':False,'financial_metrics_computed':False}
(p/'index-coverage.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
