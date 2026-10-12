"""Reviewed finite synthetic candidate checks; repository offline guards apply."""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/test_candidate.py"
assert hashlib.sha256(PATH.read_bytes()).hexdigest() == "bff2a61fb50debf361011191e87c7f4013ed695a36899ac8f66a26fd9395dfc8"
spec = importlib.util.spec_from_file_location("reviewed_gat_lifetime_checks", PATH)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
candidate = checks.candidate
test_layer_forward_first_gradients_adam_and_rng = checks.test_layer_forward_first_gradients_adam_and_rng
test_genuine_model_repeated_graph_joint_update = checks.test_genuine_model_repeated_graph_joint_update
