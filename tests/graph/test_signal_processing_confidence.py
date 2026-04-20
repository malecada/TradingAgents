from unittest.mock import MagicMock
from tradingagents.graph.signal_processing import SignalProcessor


def test_extract_confidence_high():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "HIGH"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("FINAL TRANSACTION PROPOSAL: **BUY**\nConfidence: HIGH") == "HIGH"


def test_extract_confidence_unknown_when_not_mentioned():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "UNKNOWN"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("Some text without confidence") == "UNKNOWN"


def test_extract_confidence_normalizes_whitespace_case():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "  medium  "
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("Some text ... Confidence: Medium ...") == "MEDIUM"


def test_extract_confidence_defaults_unknown_on_bad_llm_output():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "definitely not a valid label"
    sp = SignalProcessor(mock_llm)
    assert sp.extract_confidence("...") == "UNKNOWN"
