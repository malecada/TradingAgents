# Second continuation preparation — September 22, 2026

No feature worker is currently running. The first continuation stopped at
18:05:58 UTC when systemd-oomd killed it for sustained ancestor memory pressure.
All 206 completed source-day outputs remain preserved, with no new day completed.
Its failure-only terminal is recorded. See the interruption observation,
FAILURE_CLOSURE_REVIEW.md and the predecessor OOMD_DIAGNOSIS.md/FAILURE_STAGE.md.

The successor `eth-full-history-feature-panel-resume2-20260922` is being
prepared with cumulative prior 15 / cap 16. The kernel hard limit stays 6 GiB;
the lower throttle moves from 4 GiB to 6 GiB. Other memory/disk protections
and every numerical criterion stay unchanged. The same 206-day checkpoint will
be restored, then the remaining 890 dates begin on 2022-07-26. The source-checked
restoration previously took about 12.5 minutes. The 30-minute monitor follows
this recovery; no uncommitted source or claimed identity should be launched.
