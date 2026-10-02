# Unchanged neural workload under a stricter local memory cap

This prospective charter explicitly amends only the available-resource contract
for eth-paper-neural-resource-20261002-02. The original6GiB preparation, reviews
and closed01 launch are preserved byte-exact. The paper plan describes6GiB as a
cautious starting local limit; the paper does not require it. The user reports
the practical local RAM ceiling. No neural/model or test-price outcome was
observed in the predecessor: its guard stopped the bootstrap before release.
No architecture, label, seed or graph is reduced to accommodate hardware.

All original nine retained ETH weeks, requirement IDs, metadata/array identities
and seven-day windows remain. Each cell uses original CPUfloat32/seed11, PCG64
synthetic MCM(N,32), the same graph item repeated16x28, original synthetic prices
and labels, one cross-entropy backward pass and Adam(lr0.001) update. Graph
activation checkpointing remains false. Saved model/optimizer/RNG/cursor reload
is exact and performs no second step. Actual dictionary/MCM production and
financial labels are not inputs. No fit count, sample state, algorithm or
selection criterion changes; all1,420 financial fits remain pending.

The exact resource amendment selects5GiB memory.max,4.5GiB memory.high, swap0,
unchanged3GiB host reserve and8GiB startup availability (max+reserve). The
coordinator requires8.25GiB at16 observations2s apart over a60s acceptance window,
with last age at most1s before launch. This retains256MiB scheduling margin;
it is not a kernel reservation or fit guarantee. A failed or expired readiness
window creates no namespace, and further observation requires meaningful host
availability improvement. The actual guard independently rechecks8GiB during
setup and3GiB during work. No cap or reserve is relaxed during the run.

The10GiB free-disk floor,7200s whole-job and600s cooperative per-cell budgets
remain. CPU containment uses original two-CPU affinity/readback; CPUQuota is
unavailable. Policy8MiBfile/256KiBJSON/160MiBallocated/128MiBlogical/128entries/
32MiBterminaltail remains across the same three owned roots, with additional
4MiBcheckpoint/64MiBproducer-output limits and1GiB declared graph-payload limit.
These are refusal ceilings, not successful peak estimates or kernel aggregate
filesystem quotas. Configured scratch containment and original-live-parent
authority/recovery limitations remain. Loss of authority refuses mutations;
terminal and remaining-cell publication may be unavailable, with raw evidence
retained and any recovery subject to separate review.

Cells run sequentially. Error, OOM, guard expiry or uncertain cleanup stops
later scientific work; failed and all later unavailable cells remain in the
denominator. First fatal identity/cause is preserved. No automatic retry/resume
or same-identity relaunch is allowed. The closed01 identity is permanently spent
operationally; all33 historical claims and exposed samples remain spent. This
02 identity uses the same unused single neural-resource allocation under exact
reviewed62=33+12body+15financial+1neuralresource+1otherresource, not a refund or
additional financial trial. Once claimed, failure spends that allocation; any
later empirical successor needs another cumulative review.

Successful unchanged workload under5GiB supports observed execution within a
<=6GiB ceiling. It does not measure the old6GiB/5GiBhigh reclaim or timing
behavior. Failure at5GiB does not establish failure at6GiB. Per-cell/whole-job
peak, actual kernel controls, events, walltime, bytes and exact reload evidence
need independent verification. Neither success nor failure supplies numerical
agreement, chronological multiweek capacity, GPU parity or an economic edge.

Before release: independently accept this exact resource/budget/charter/job/
scheduling/helper amendment, freeze and review complete source/runtime and final
gate with original48inputs/ancestorchain plus explicit metadata evidence, commit
and externally back up exact files, pass actual lifecycle admission and claim/
RPC sizes, then obtain new in-process readiness and immediate fresh disk/OS
checks. Array bodies are revalidated by the owned worker before use. Current
preparation is NONEXECUTABLE while source/runtime fields are null. No paid or
external resources, credentials, provider/author contact or trading are selected.
