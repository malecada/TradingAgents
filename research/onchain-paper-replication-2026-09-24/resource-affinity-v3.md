# Pre-result resource enforcement amendment v3

The user cgroup hierarchy delegates memory and pids, but not cpu/cpuset. Synthetic
probe01 refused release because cpu.max was absent and cleaned up. No host
configuration, privilege escalation or empirical execution followed that failure.

The two-CPU quantitative limit is retained using inherited sched_setaffinity on
exactly two logical CPUs. Before release the ready child PID must appear within
the verified run cgroup with that exact mask. Every sampled thread in the run
cgroup and all nested cgroups must have a nonempty subset of the same two CPUs;
a widened mask stops the unit. Ordinary children inherit the restriction. This
is affinity enforcement for the reviewed cooperative code, not cgroup CPU quota
enforcement or protection from malicious mask changes between observations.
Independent resource review accepted this explicit mechanism deviation. No other
research module may widen affinity. Memory6GiB, high5GiB, swap0 remain kernel
cgroup controls; host reserve3GiB, each used-volume disk floor20GiB and wall bounds
are unchanged and checked before release and during the job.

Evidence under resources/: probe02 retained an inline synthetic fixture syntax
failure; probe03 passed with child and three threads (six observed PID/TIDs), all
masked to CPUs0,1,20.1MiB sampled cgroup peak and verified cleanup. Subsequent
synthetic-sigterm-01 (including second signal), synthetic-monitor-loss-01 and
synthetic-affinity-widen-01 all stopped the complete cgroup, including a child
that created a new session. Observer terminals verify empty cgroups. Monitor-loss
correctly has no monitor final.json; child_exit.json records lost lease, and a
separate observer-terminal.json supplies termination/cleanup evidence. These
synthetic identities are retained and may not be overwritten/relaunched.

Worker admission must bind the exact command, boot/lease/cgroup, required volume
identities and approved time ceiling. Each actual claim still needs its committed
registration and release review. This amendment does not release a scientific run.
