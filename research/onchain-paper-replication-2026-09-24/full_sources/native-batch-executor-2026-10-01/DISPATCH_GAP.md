# Concrete production dispatch boundary

Read-only inspection during check01 identified the remaining production boundary.
The accepted native map can be passed to maintained run.execute_batch directly.
That is the current synthetic test. The ordinary guarded worker still calls
job_payload.execute_fit_payload; its produce branch calls
registered_features.prepare_registered_features, which creates a FeatureJournal,
runs prepare_features, then seals it. The reuse branch calls
reuse_registered_features. Neither branch selects the separately accepted
current-owner native path. Passing the native-feature policy key alone therefore
does not change the producer used by the ordinary guarded worker.

The next production integration must explicitly select and validate the new
producer in both plan and execution-job routes before any numerical allocation.
It must retain the existing population and batch preflight checks, instantiate one
actual FeatureJournal/workload/pair owner, publish sampler and dictionary proofs,
obtain the actual dictionary ticket, and publish required MCM/graph components
before native_map.prepare performs the once-only sealing transition. The returned
PreparedFeatures can then use the already maintained execute_batch consumer.
This needs a real orchestration function; a caller-created Receipt or manual
patch of the old producer cannot provide admission. Existing completed data are
reused only through their explicitly admitted history path.

The current components accept resident GraphSnapshot parents. Connecting this
route does not itself solve mapped parent populations or full-history admission.
job.required_sources pins the maintained package but does not discover dated
full_sources modules automatically: the selected route must include their exact
transitive source closure in registration and keep imports from one consistent
module chain because owner/ticket class identity is checked. The native map
retains the current owner through its terminal lease while fitting proceeds.
Producer scope and lifetime must therefore span the batch; leaving a mapped graph
context before fitting would invalidate retained ownership.

Failure handling must keep partial publications and terminal numerical journals;
an error after sealing cannot invoke the old prepare_registered_features path.
Completed or failed representation identities never become fresh attempts.
Missing historical/cold reuse remains a separately reported requirement.
No production source change or empirical execution is claimed by this inspection.
