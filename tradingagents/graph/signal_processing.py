# TradingAgents/graph/signal_processing.py

from typing import Any


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: Any):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Extracted rating (BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, or SELL)
        """
        messages = [
            (
                "system",
                "You are an efficient assistant that extracts the trading decision from analyst reports. "
                "Extract the rating as exactly one of: BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, SELL. "
                "Output only the single rating word, nothing else.",
            ),
            ("human", full_signal),
        ]

        return self.quick_thinking_llm.invoke(messages).content

    def extract_confidence(self, full_signal: str) -> str:
        """Infer confidence level (HIGH/MEDIUM/LOW) from trader output.

        The trader prompt asks for a HIGH/MEDIUM/LOW label but frequently
        omits it. Rather than fall back to UNKNOWN, this method asks the
        quick LLM to *infer* confidence from the conviction strength of
        the text itself — strong directional commitment with clear
        thesis = HIGH; hedged / "monitor closely" / "conflicting signals"
        language = LOW; balanced reasoning with a clear lean = MEDIUM.

        Rubric is applied to the full trader/portfolio-manager output, so
        a missing literal label no longer forces UNKNOWN.

        Args:
            full_signal: Trader/portfolio-manager text.

        Returns:
            One of {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}. UNKNOWN is only
            returned when the LLM response is malformed.
        """
        messages = [
            (
                "system",
                "You are a trading-decision confidence rater. Read the trader's "
                "output and rate how confident the decision is, on the following "
                "rubric:\n"
                "  HIGH  — strong directional commitment, clear thesis, decisive "
                "language ('execute immediate', 'strong conviction', 'clear buy/sell signal'), "
                "few or no caveats. If the trader explicitly states 'Confidence: HIGH', return HIGH.\n"
                "  MEDIUM — clear lean in one direction but acknowledges meaningful "
                "counter-evidence or risks; recommends moderate sizing / staged entry. "
                "If the trader explicitly states 'Confidence: MEDIUM', return MEDIUM.\n"
                "  LOW   — hedged, HOLD with 'conflicting signals', 'monitor closely', "
                "'wait for confirmation', 'conservative position sizing', or a decision driven "
                "by uncertainty rather than evidence. If the trader explicitly states "
                "'Confidence: LOW', return LOW.\n"
                "Prefer an explicit label (HIGH/MEDIUM/LOW) when the trader provides one; "
                "otherwise infer from conviction strength per the rubric.\n"
                "Output exactly one word: HIGH, MEDIUM, or LOW. No other text.",
            ),
            ("human", full_signal),
        ]

        raw = self.quick_thinking_llm.invoke(messages).content
        cleaned = (raw or "").strip().upper()
        # Strip punctuation / markdown the LLM may have added
        for sep in (".", ",", "*", "`", ":", ";"):
            cleaned = cleaned.replace(sep, "")
        cleaned = cleaned.strip()
        # Handle cases like "HIGH CONFIDENCE" or "HIGH." robustly
        first = cleaned.split()[0] if cleaned else ""
        if first in {"HIGH", "MEDIUM", "LOW"}:
            return first
        return "UNKNOWN"
