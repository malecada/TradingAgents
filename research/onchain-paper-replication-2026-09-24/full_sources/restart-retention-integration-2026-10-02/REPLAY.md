# Exact source replay representation

Each ownerNN-manifest.json binds every file in its retained ownerNN-source copy.
The corresponding ownerNN-replay.json names a committed base and identifies each
file as either base_commit or delta. ownerNN-delta contains every differing or
new file, including untracked package modules, tests and support files. The base
is a reconstruction reference, not a claim that the tested dirty candidate was
committed. Every original full source copy and failed log remains locally intact.

To reconstruct, create a fresh empty directory and process exactly the replay
manifest's file set. For base_commit entries obtain bytes with `git show
<base_commit>:<path>`; for delta entries copy the same relative path from the delta
directory. Verify every SHA256 and byte extent against the manifest before use.
Do not overlay the delta onto an unrestricted full checkout: additional package
Python files can change the dynamic required_sources closure. This record grants
no permission to execute historical, empirical or network jobs. A named synthetic
pytest command still needs its documented pinned runtime and isolation profile.

Source copying uses snapshot_source.py; compact backup representation uses
replay_bundle.py. Neither executes experiments. Source manifests are never
rewritten after a run. Full copies are excluded from the proposed Git evidence
checkpoint only to avoid repeated storage of already committed unchanged bytes.
