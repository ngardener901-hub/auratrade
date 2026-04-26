"""
Journal Analyzer — AI Trade Pattern Matching
--------------------------------------------
Analyzes completed trades against the 11-chart training set and
produces human-readable explanations for journal review.

Pattern database is embedded inline (no external DB needed).
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class PatternExample:
    id: int
    name: str
    regime: str                         # "BLUE" or "RED"
    direction: str                        # "long" or "short"
    key_features: List[str]
    success_factors: List[str]
    notes: str


# ═══════════════════════════════════════════════════════════════════════════════
#  11-CHART TRAINING DATABASE (embedded)
# ═══════════════════════════════════════════════════════════════════════════════

PATTERN_DATABASE: List[PatternExample] = [
    PatternExample(
        id=1,
        name="Tuesday VWAP Reclaim Long",
        regime="BLUE",
        direction="long",
        key_features=[
            "price_below_vwap_pre_open",
            "london_low_sweep",
            "bullish_fvg_post_sweep",
            "vwap_reclaim",
            "retest_at_vwap_confluence",
        ],
        success_factors=[
            "London Low provided structural support",
            "Bullish FVG formed immediately after sweep",
            "VWAP reclaimed = trend alignment confirmed",
            "Entry on retest gave 2R+ expansion to prior session high",
        ],
        notes="Classic BLUE regime setup. Mid-week momentum after London sweep.",
    ),
    PatternExample(
        id=2,
        name="Wednesday Expansion Long",
        regime="BLUE",
        direction="long",
        key_features=[
            "prev_session_high_sweep",
            "small_pullback_bullish_fvg",
            "vwap_above_fvg",
            "tight_retest",
        ],
        success_factors=[
            "Prior session high was liquidity pool",
            "Displacement FVG showed buyer aggression",
            "VWAP stayed above FVG = strong trend",
        ],
        notes="Expansion play. Previous session high as target.",
    ),
    PatternExample(
        id=3,
        name="Mid-Week Long, VWAP Reclaim + FVG",
        regime="BLUE",
        direction="long",
        key_features=[
            "london_low_sweep_and_reclaim",
            "bullish_fvg_formed",
            "retest_at_vwap",
            "ema9_support",
        ],
        success_factors=[
            "Price reclaimed London Low",
            "Bullish FVG formed with 6-tick displacement",
            "Retest occurred at confluence with VWAP",
            "9-EMA held as trailing support",
        ],
        notes="The textbook 'Holy Grail' — all 4 criteria met.",
    ),
    PatternExample(
        id=4,
        name="Thursday Breakout Continuation",
        regime="BLUE",
        direction="long",
        key_features=[
            "pre_market_high_sweep",
            "bullish_fvg_above_vwap",
            "no_retest_immediate_run",
            "pyramid_on_second_fvg",
        ],
        success_factors=[
            "Pre-market high sweep cleared stops",
            "Immediate displacement without deep retest",
            "Second FVG allowed pyramid add",
        ],
        notes="Aggressive BLUE play. Pyramid added 1 contract at 1R profit.",
    ),
    PatternExample(
        id=5,
        name="Tuesday Afternoon Pullback Long",
        regime="BLUE",
        direction="long",
        key_features=[
            "morning_expansion",
            "pullback_to_vwap",
            "bullish_fvg_on_pullback",
            "continuation_to_highs",
        ],
        success_factors=[
            "Morning trend established direction",
            "VWAP held on pullback = institutional interest",
            "Bullish FVG in pullback = buyer absorption",
        ],
        notes="Afternoon session continuation. Entered on VWAP + FVG confluence.",
    ),
    PatternExample(
        id=6,
        name="Monday Trap Short",
        regime="RED",
        direction="short",
        key_features=[
            "london_high_breakout_fake",
            "price_reclaimed_below_london_high",
            "bearish_fvg_at_reclaim",
            "vwap_rejection",
        ],
        success_factors=[
            "False breakout above London High trapped longs",
            "Reclaim below London High = structure shift",
            "Bearish FVG formed at VWAP rejection",
            "Target = VWAP (tight, no pyramiding)",
        ],
        notes="Classic RED regime Monday trap. Tight target, quick exit.",
    ),
    PatternExample(
        id=7,
        name="Friday Reversal Short",
        regime="RED",
        direction="short",
        key_features=[
            "overnight_high_sweep",
            "bearish_engulfing_post_sweep",
            "bearish_fvg_displacement",
            "vwap_cross_down",
        ],
        success_factors=[
            "Overnight high sweep in early session",
            "Bearish FVG after sweep = seller control",
            "VWAP crossed and held as resistance",
        ],
        notes="Friday fade. End-of-week profit taking pattern.",
    ),
    PatternExample(
        id=8,
        name="Monday Morning Fade",
        regime="RED",
        direction="short",
        key_features=[
            "gap_up_open",
            "prev_nyam_high_sweep",
            "immediate_reversal",
            "bearish_fvg_with_vwap_below",
        ],
        success_factors=[
            "Gap up swept prior NYAM high = liquidity target",
            "Immediate reversal showed seller absorption",
            "Bearish FVG confluence with VWAP below",
        ],
        notes="Gap-and-crap Monday. RED regime characteristic.",
    ),
    PatternExample(
        id=9,
        name="Friday Trap Long (Rare)",
        regime="RED",
        direction="long",
        key_features=[
            "london_low_sweep",
            "quick_reclaim",
            "small_bullish_fvg",
            "vwap_bounce",
        ],
        success_factors=[
            "London Low sweep flushed weak longs",
            "Quick reclaim showed demand at level",
            "Small FVG + VWAP bounce = scalp only",
        ],
        notes="Counter-trend RED play. Only for experienced discretion.",
    ),
    PatternExample(
        id=10,
        name="Wednesday VWAP Failed Break Short",
        regime="BLUE",
        direction="short",
        key_features=[
            "vwap_test_from_below",
            "failed_break_above_vwap",
            "bearish_fvg_at_vwap",
            "trend_still_up_but_chop",
        ],
        success_factors=[
            "VWAP rejection in BLUE = caution flag",
            "Bearish FVG at VWAP = short-term fade",
            "Small size, tight stop, quick target",
        ],
        notes="BLUE regime counter-trend. Only taken when confidence > 75%.",
    ),
    PatternExample(
        id=11,
        name="Thursday High-Confidence Pyramid",
        regime="BLUE",
        direction="long",
        key_features=[
            "first_trade_already_1r",
            "second_bullish_fvg_formed",
            "same_direction",
            "vwap_far_below_add",
        ],
        success_factors=[
            "First position profitable = edge confirmed",
            "Second FVG at higher level = trend strength",
            "Pyramid added within risk limits",
        ],
        notes="Pyramiding example. Added 1 MNQ contract at +1.2R on first position.",
    ),
]


def analyze_trade(trade: Dict[str, Any], regime: str, pattern_db: Optional[List[PatternExample]] = None) -> str:
    """
    AI analysis: match a completed trade against the 11 training examples.

    Parameters
    ----------
    trade : dict
        Must contain keys: direction, entry_price, exit_price, pnl,
        fvg_direction, sweep_level, vwap_at_entry, ema9_aligned.
    regime : str
        "BLUE" or "RED"
    pattern_db : list, optional
        Override default pattern database.

    Returns
    -------
    str
        Human-readable analysis with pattern match and success factors.
    """
    if pattern_db is None:
        pattern_db = PATTERN_DATABASE

    # Filter to regime-relevant patterns
    candidates = [p for p in pattern_db if p.regime == regime]
    if not candidates:
        candidates = pattern_db

    # Score each pattern by feature overlap
    scored_patterns = []
    trade_features = _extract_trade_features(trade)

    for pattern in candidates:
        score = _pattern_similarity(pattern, trade_features)
        scored_patterns.append((score, pattern))

    scored_patterns.sort(key=lambda x: x[0], reverse=True)
    best_score, best_pattern = scored_patterns[0]

    # Build narrative
    lines = []
    lines.append(f"Pattern Match: #{best_pattern.id} – {best_pattern.name}")
    lines.append(f"Match Confidence: {best_score:.0%}")
    lines.append("")
    lines.append("Success Factors:")
    for factor in best_pattern.success_factors:
        match_indicator = "[MATCH]" if any(kw in factor.lower() for kw in trade_features) else "[context]"
        lines.append(f"  {match_indicator} {factor}")
    lines.append("")
    lines.append(f"Notes: {best_pattern.notes}")

    if trade.get("pnl", 0) > 0:
        lines.append(f"Result: +${trade['pnl']:.2f} profit. Pattern validation strengthened.")
    else:
        lines.append(f"Result: ${trade['pnl']:.2f} loss. Review deviation from pattern criteria.")

    return "\n".join(lines)


def _extract_trade_features(trade: Dict[str, Any]) -> List[str]:
    """Extract searchable feature strings from a trade record."""
    features = []
    direction = trade.get("direction", "")
    if direction:
        features.append(direction.lower())
    if trade.get("fvg_direction"):
        features.append(trade["fvg_direction"].lower())
    if trade.get("sweep_level"):
        features.append(trade["sweep_level"].lower().replace("_", " "))
    if trade.get("vwap_aligned"):
        features.append("vwap")
    if trade.get("ema9_aligned"):
        features.append("ema9")
    if trade.get("pyramid"):
        features.append("pyramid")
    return features


def _pattern_similarity(pattern: PatternExample, trade_features: List[str]) -> float:
    """
    Compute similarity score between pattern features and trade.
    Uses keyword overlap + fuzzy string matching.
    """
    if not pattern.key_features:
        return 0.0

    pattern_text = " ".join(pattern.key_features).lower()
    trade_text = " ".join(trade_features).lower()

    # Keyword hits
    hits = sum(1 for feat in trade_features if feat in pattern_text)
    keyword_score = hits / len(pattern.key_features) if pattern.key_features else 0

    # Fuzzy similarity
    fuzzy_score = SequenceMatcher(None, pattern_text, trade_text).ratio()

    return round(keyword_score * 0.7 + fuzzy_score * 0.3, 3)


def get_pattern_by_id(pattern_id: int) -> Optional[PatternExample]:
    """Return a specific pattern from the database."""
    for p in PATTERN_DATABASE:
        if p.id == pattern_id:
            return p
    return None


def list_patterns(regime: Optional[str] = None) -> List[str]:
    """Return formatted list of all patterns (optionally filtered by regime)."""
    patterns = PATTERN_DATABASE if regime is None else [p for p in PATTERN_DATABASE if p.regime == regime]
    return [f"#{p.id} [{p.regime}] {p.name} — {p.direction}" for p in patterns]
