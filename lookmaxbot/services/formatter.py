import re

TIER_EMOJI = {
    "npc": "💀",
    "below average": "😔",
    "average": "😐",
    "above average": "🙂",
    "attractive": "😎",
    "chad": "👑",
    "gigachad": "🗿",
}

BAR_LENGTH = 10


def _score_bar(score: float) -> str:
    filled = round(score)
    return "█" * filled + "░" * (BAR_LENGTH - filled)


def _extract_score(text: str) -> float | None:
    m = re.search(r"SCORE:\s*(\d+(?:\.\d+)?)/10", text)
    return float(m.group(1)) if m else None


def _extract_tier(text: str) -> str:
    m = re.search(r"TIER:\s*(.+)", text)
    return m.group(1).strip() if m else "Unknown"


def _strip_score_tier(text: str) -> str:
    """Remove SCORE and TIER lines — they're shown in the header."""
    lines = [
        line for line in text.split("\n")
        if not line.startswith("SCORE:") and not line.startswith("TIER:")
    ]
    return "\n".join(lines).strip()


def format_result(
    analysis: str,
    advice: str,
    user_name: str,
    detailed: bool = False,
) -> tuple[str, str]:
    """
    Returns (msg1, msg2):
      msg1 — анализ с заголовком и скором
      msg2 — roadmap советов (отдельное сообщение)
    """
    score = _extract_score(analysis)
    tier = _extract_tier(analysis)
    tier_emoji = TIER_EMOJI.get(tier.lower(), "⚡")

    # ── Сообщение 1: анализ ──────────────────────────────────────────────────
    if score is not None:
        bar = _score_bar(score)
        header = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔬 *LOOKSMAX ANALYSIS*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 *{user_name}*\n\n"
            f"📊 *SCORE: {score}/10*\n"
            f"`{bar}`\n\n"
            f"{tier_emoji} *TIER: {tier}*\n\n"
        )
    else:
        header = f"🔬 *LOOKSMAX ANALYSIS — {user_name}*\n\n"

    body = _strip_score_tier(analysis)
    label = "🔥 *DETAILED ROADMAP* ниже 👇" if detailed else "🗺 *LOOKSMAX ROADMAP* ниже 👇"
    msg1 = header + body + f"\n\n{label}"

    # ── Сообщение 2: советы ──────────────────────────────────────────────────
    prefix = "🔬 *ADVANCED LOOKSMAX PLAN*\n\n" if detailed else "🗺 *ТВОЙ LOOKSMAX ROADMAP*\n\n"
    msg2 = prefix + advice.strip()

    return msg1, msg2
