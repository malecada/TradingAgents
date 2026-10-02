# Independent final fit/checkpoint review

Accepted as bounded synthetic verification of actual compact native features through the maintained scaler, batch factory, fitting, prediction and checkpoint-loading APIs. REVIEW_INITIAL.md is preserved. Raw check01 reports **1 passed in 747.61 seconds**; that single test executes both registered synthetic tasks. The current test and directly reviewed source hashes match the initial inspection. No checks, numerical replays or empirical jobs were rerun by the reviewer.

The actual fresh compact producer supplies the feature map. Both synthetic cell names and explicit model/training inputs are registered before claim. Maintained fit_scaler uses a table reconstructed only from training-input prices, with its unique-date/fold-window selection. Both direction and regression execute maintained batch_factory, two fit_cell epochs with batch size one, and predict_cell. Epoch accounting covers all supplied training examples. Returned checkpoint hashes match the manifest file; load_checkpoint verifies artifact members and expected provenance before restoring the model, optimizer and RNG state. The restored epoch/batch/logs, every model-state tensor and prediction tensors match exactly. Both duplicate fit attempts refuse already-claimed cells.

After each task the test releases its returned model/checkpoint references, requires zero tracked native tensor-wrapper bytes after collection, verifies unchanged saved feature hashes and calls full compact producer finalization. No material defect remains against those assertions.

The accepted claim is deliberately limited. Mean/std and repeated-date consistency are not independently reconstructed by this test. Checkpoint model weights, predictions and cursor/logs are compared exactly; optimizer/RNG values or resumed-update parity are not independently compared. The test does not explicitly join fit complete.json to the returned checkpoint. Provenance is supplied directly to the lower-level fit/checkpoint API, so full evaluate_cell scientific config/cell/scaler/output validation and execute_batch are not covered. No independent prediction metrics or outcome ledger is produced by this test.

The fixture uses two motifs, two time steps, two epochs and a mocked OS guard. It is not actual OS-guarded fit dispatch, paper-level numerical parity, full-size resource feasibility or empirical admission. Zero tracked wrapper bytes does not prove release of aliases, autograd/model storage, Python allocations or RSS; scientific originals remain resident. Fixtures are temporary: the retained evidence is test/source/log history, not a claim that checkpoint blobs themselves were retained. Production settings and financial exposure are unchanged.

Verified direct SHA-256 bindings:

- test_compact_native_fit.py: `b5643819da569bca454b49829599a8f1ec393dafad8421dc6864ba8e999ffafc`
- training.py: `5c0380de62c670d356ea3546c7b81eed4ccab55a886bc27b6a1bbfd75c2c3369`
- checkpoints.py: `74e7bd16d4331cbac45143884e1f35a52687b19280c214457834b0cf19a457bc`
- dataset.py: `c8d701b5646395bb94e5037aefcc2d0d29a55de95cca05e019ce35d3f53561df`
- evaluation.py: `b3af7cf6b71f8adcdd762eb471abb66d8fdd00f20087aeff377447d51a854b29`
- check01.log: `79a6431db674c10c96082f4999ae958ce0f9030400622ac039511559e5824235`
