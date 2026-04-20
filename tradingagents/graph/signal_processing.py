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
        """Extract confidence label (HIGH/MEDIUM/LOW) from trader output.

        The trader prompt instructs the LLM to state confidence as HIGH /
        MEDIUM / LOW alongside its decision. This method uses the quick LLM
        to parse that label, returning 'UNKNOWN' when it cannot be found.

        Args:
            full_signal: Trader/portfolio-manager text that may contain a
                confidence label.

        Returns:
            One of {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}.
        """
        messages = [
            (
                "system",
                "You are an efficient assistant that extracts the confidence "
                "level from a trading decision text. The text may contain a "
                "label such as 'Confidence: HIGH' or 'HIGH confidence'. "
                "Return exactly one of: HIGH, MEDIUM, LOW, UNKNOWN. "
                "Return UNKNOWN if no confidence is mentioned or it is unclear. "
                "Output only the single word, nothing else.",
            ),
            ("human", full_signal),
        ]

        raw = self.quick_thinking_llm.invoke(messages).content
        cleaned = (raw or "").strip().upper()
        if cleaned in {"HIGH", "MEDIUM", "LOW"}:
            return cleaned
        return "UNKNOWN"
