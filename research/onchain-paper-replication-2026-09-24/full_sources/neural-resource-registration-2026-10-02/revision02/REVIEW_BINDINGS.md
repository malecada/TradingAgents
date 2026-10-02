# Independent revision02 binding review

Disposition: accepted as metadata preparation only. No final gate, runtime/source freeze, empirical admission or namespace reservation is accepted.

All six members of `SHA256SUMS.bindings01` were independently hashed. Manifest SHA256: `21366ccc1cfc837a9986c36e8f915b6677935b7f00575f9df945b65498e0e37e`. Principal reviewed bindings:

| File | SHA256 |
| --- | --- |
| bindings01.json | 4e6d6cf24a4986c7036d024ea1eb1436047e4a2de0da80bd49d9aabd73f1faa8 |
| environment.json | 3a97a20ba8058cac81c8c62a7ba3596aac2fe4deb17627d0aa57bf53a93b86dc |
| execution-workspace.json | beb469c0d9e8255e1a021005b2b93849a4efd53b52af9e3768732cfe5c70711f |
| parent-experiment.json | 5667a923fbfdd14094f91bca366b1bf87cdc2c375b251e415123502075bec424 |

The saved parent experiment equals the complete original `experiment` object in the immutable `eth-paper-resource-pilot-20260924-02` claim, without substituting a newly drafted parent configuration. Claim SHA256 `05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca` and failed-terminal SHA256 `3d318717ff7adecb0f07b9db6f3d1bd2e24e0c77705c3e07062cd4b075f8d7f2` match actual bytes; terminal experiment/status/claim joins agree, and no complete terminal is present. The family's exact object matches the retained draft registry. Equality here concerns the complete parsed experiment value serialized into a new file, not a claim that its textual substring formatting was copied verbatim from claim.json.

The exact accepted extension, allocation and independent review pins agree with their actual files: extension `d5104e0b2be17af97e1bbfc622a3bf081e1156829dd2d034021795b06b968cd5`, allocation `98936c0eb8da31b3054191e12228ab35872d9d41f35c250968b6d7cf0fe511c9`, review `0bae2075a5ab7133fc76541576f48afdb33e7a647835ef9053ae2dcaf5921985`. Their earlier budget-only scope remains unchanged; recording these references does not invoke adoption.

The environment object has exactly the public fields produced by maintained `environment.inventory(..., include_torch=True)`, whose recorded source hash was verified. Using only standard-library metadata, the reviewer independently compared Python3.13.13,12 host CPUs, the lockfile hash and installed distribution versions: NumPy2.3.0, SciPy1.17.1, PyArrow23.0.1, Torch2.10.0 and scikit-learn1.7.2. Reading Torch's public version constants confirms `2.10.0+cu128` and build12.8. The captured `cuda_available=false` observation was not reprobed: the reviewer did not import Torch or query CUDA. Public version metadata does not prove runtime binary identity, numerical equivalence or continued environment availability; the final registered runtime comparison remains necessary.

Workspace root, ledger, artifact directory and Git common directory match the current path definitions and a read-only Git common-directory query. This is a mapping check, not storage reservation, external backup proof or admission of all mapped bytes. The designated neural experiment's lifecycle/launch/producer namespaces were independently absent, including dangling symlinks. Their absence is point-in-time evidence and does not reserve the name.

The capture script and its successful raw log were inspected but not rerun. This review read compact metadata, public source/version text and hashes only. No execution modules, model, Torch, admission, arrays, guard, historical run or network action were invoked; no old metadata was modified. Final physical-policy implementation and limits, exact charter/job/gate, complete committed source/runtime closure, independent gate review and fresh host/input/admission checks remain unresolved. Moving package sources cannot acquire a freeze merely by retaining these bindings.
