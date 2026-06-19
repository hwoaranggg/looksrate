"""
Генератор PNG-карточки результата looksmax-анализа.
Карточка 1080×1350 (формат Instagram/TikTok Stories 4:5).
"""
import io
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ── Шрифты ───────────────────────────────────────────────────────────────────
FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ── Палитра ───────────────────────────────────────────────────────────────────
BG_TOP      = (10,  10,  18)   # почти чёрный
BG_BOTTOM   = (18,  12,  35)   # тёмно-фиолетовый
ACCENT      = (138,  43, 226)  # фиолетовый
ACCENT2     = (75,   0, 130)   # индиго
GOLD        = (255, 200,  50)  # золотой для скора
WHITE       = (255, 255, 255)
GREY        = (170, 170, 190)
GREEN       = (80,  220, 100)
RED         = (255,  80,  80)
BAR_FILLED  = (138,  43, 226)
BAR_EMPTY   = (45,   35,  60)

# ── Tier цвета ────────────────────────────────────────────────────────────────
TIER_COLORS = {
    "npc":           (120, 120, 120),
    "below average": (180,  80,  80),
    "average":       (200, 160,  60),
    "above average": (80,  180,  80),
    "attractive":    (60,  180, 200),
    "chad":          (138,  43, 226),
    "gigachad":      (255, 200,  50),
}

W, H = 1080, 1350


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size)


def _gradient_bg(draw: ImageDraw.ImageDraw) -> None:
    """Вертикальный градиент фона."""
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _score_bar(draw: ImageDraw.ImageDraw, x: int, y: int, score: float,
               bar_w: int = 680, bar_h: int = 22) -> None:
    """Прогресс-бар скора."""
    segments = 10
    seg_w = bar_w // segments
    gap = 4
    filled = round(score)
    for i in range(segments):
        color = BAR_FILLED if i < filled else BAR_EMPTY
        rx = x + i * seg_w + gap // 2
        draw.rounded_rectangle(
            [rx, y, rx + seg_w - gap, y + bar_h],
            radius=4, fill=color,
        )


def _breakdown_bar(draw: ImageDraw.ImageDraw, x: int, y: int, score: float,
                   max_w: int = 220, bar_h: int = 10) -> None:
    """Маленький бар для breakdown-строки."""
    filled_w = int(max_w * score / 10)
    draw.rounded_rectangle([x, y, x + max_w, y + bar_h], radius=3, fill=BAR_EMPTY)
    if filled_w > 0:
        draw.rounded_rectangle([x, y, x + filled_w, y + bar_h], radius=3, fill=BAR_FILLED)


def _extract(text: str, pattern: str, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else default


def _parse_score(val: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", val)
    return float(m.group(1)) if m else None


def _parse_breakdown(analysis: str) -> list[tuple[str, float, str]]:
    """Возвращает [(label, score, comment), ...]"""
    pattern = re.compile(
        r"•\s*(.+?):\s*(\d+(?:\.\d+)?)/10\s*[—-]\s*(.+)"
    )
    results = []
    for m in pattern.finditer(analysis):
        label   = m.group(1).strip()
        score   = float(m.group(2))
        comment = m.group(3).strip()
        # Укорачиваем лейблы для карточки
        label = label.replace("& ", "& ").replace("Facial Harmony", "Harmony")
        results.append((label, score, comment))
    return results[:7]  # максимум 7 строк


def _parse_bullets(analysis: str, marker: str) -> list[str]:
    """Парсит блок POSITIVES или NEGATIVES."""
    section = re.search(
        rf"{marker}:\s*\n((?:[+\-•].*\n?)+)", analysis, re.IGNORECASE
    )
    if not section:
        return []
    lines = []
    for line in section.group(1).strip().split("\n"):
        line = re.sub(r"^[+\-•]\s*", "", line).strip()
        if line:
            lines.append(line)
    return lines[:3]


def generate_card(analysis: str, user_name: str) -> bytes:
    """
    Генерирует PNG-карточку и возвращает bytes.
    """
    img  = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    _gradient_bg(draw)

    # ── Декоративные элементы ─────────────────────────────────────────────────
    # Верхняя светящаяся полоса
    draw.rectangle([0, 0, W, 5], fill=ACCENT)

    # Фоновые круги (декор)
    for cx, cy, r, opacity in [(900, 200, 280, 18), (150, 1100, 200, 12)]:
        for dr in range(0, r, 8):
            a = max(0, opacity - dr // 10)
            c = tuple(min(255, int(v * a / 100 + BG_BOTTOM[i] * (1 - a / 100)))
                      for i, v in enumerate(ACCENT))
            draw.ellipse([cx-r+dr, cy-r+dr, cx+r-dr, cy+r-dr], outline=c, width=1)

    # ── Парсинг данных ────────────────────────────────────────────────────────
    score_str = _extract(analysis, r"SCORE:\s*(\d+(?:\.\d+)?)/10")
    score     = _parse_score(score_str) or 5.0
    tier      = _extract(analysis, r"TIER:\s*(.+)")
    tier_col  = TIER_COLORS.get(tier.lower(), WHITE)
    verdict   = _extract(analysis, r"VERDICT:\s*(.+?)(?:\n|$)")
    breakdown = _parse_breakdown(analysis)
    positives = _parse_bullets(analysis, "POSITIVES")
    negatives = _parse_bullets(analysis, "NEGATIVES")

    y = 52  # текущая позиция по Y

    # ── Заголовок ─────────────────────────────────────────────────────────────
    draw.text((W // 2, y), "LOOKSMAX", font=_font(52, bold=True),
              fill=WHITE, anchor="mt")
    y += 58
    draw.text((W // 2, y), "AI ANALYSIS", font=_font(22),
              fill=ACCENT, anchor="mt")
    y += 44

    # Имя пользователя
    name_display = f"@{user_name}" if not user_name.startswith("@") else user_name
    draw.text((W // 2, y), name_display, font=_font(28, bold=True),
              fill=GREY, anchor="mt")
    y += 54

    # ── Разделитель ───────────────────────────────────────────────────────────
    draw.rectangle([80, y, W - 80, y + 1], fill=ACCENT2)
    y += 24

    # ── Скор ─────────────────────────────────────────────────────────────────
    draw.text((W // 2, y), f"{score:.1f}", font=_font(110, bold=True),
              fill=GOLD, anchor="mt")
    y += 118
    draw.text((W // 2, y), "OUT OF 10", font=_font(18),
              fill=GREY, anchor="mt")
    y += 38

    # Прогресс-бар скора
    bar_w = 680
    bar_x = (W - bar_w) // 2
    _score_bar(draw, bar_x, y, score, bar_w=bar_w)
    y += 48

    # ── Tier badge ────────────────────────────────────────────────────────────
    tier_text = tier.upper() if tier else "UNKNOWN"
    badge_w, badge_h = 340, 52
    badge_x = (W - badge_w) // 2
    draw.rounded_rectangle(
        [badge_x, y, badge_x + badge_w, y + badge_h],
        radius=26, fill=(*tier_col, 30) if False else (30, 20, 50),
        outline=tier_col, width=2,
    )
    draw.text((W // 2, y + badge_h // 2), tier_text,
              font=_font(26, bold=True), fill=tier_col, anchor="mm")
    y += badge_h + 30

    # ── Разделитель ───────────────────────────────────────────────────────────
    draw.rectangle([80, y, W - 80, y + 1], fill=ACCENT2)
    y += 22

    # ── Breakdown ─────────────────────────────────────────────────────────────
    if breakdown:
        draw.text((80, y), "BREAKDOWN", font=_font(20, bold=True), fill=ACCENT)
        y += 34
        for label, bscore, comment in breakdown:
            # Лейбл + скор
            draw.text((80, y), label, font=_font(18, bold=True), fill=WHITE)
            draw.text((W - 80, y), f"{bscore:.1f}", font=_font(18, bold=True),
                      fill=GOLD, anchor="ra")
            y += 22
            # Маленький бар
            _breakdown_bar(draw, 80, y, bscore)
            y += 20
            # Комментарий (обрезаем если длинный)
            short_comment = comment[:72] + "…" if len(comment) > 72 else comment
            draw.text((80, y), short_comment, font=_font(14), fill=GREY)
            y += 28

    # ── Разделитель ───────────────────────────────────────────────────────────
    draw.rectangle([80, y, W - 80, y + 1], fill=ACCENT2)
    y += 22

    # ── Плюсы и минусы (два столбца) ─────────────────────────────────────────
    col_w = (W - 200) // 2
    lx, rx = 80, 80 + col_w + 40

    if positives or negatives:
        draw.text((lx, y), "✦ STRENGTHS", font=_font(17, bold=True), fill=GREEN)
        draw.text((rx, y), "✦ WEAKNESSES", font=_font(17, bold=True), fill=RED)
        y += 30

        max_rows = max(len(positives), len(negatives))
        for i in range(max_rows):
            if i < len(positives):
                txt = positives[i][:42] + "…" if len(positives[i]) > 42 else positives[i]
                draw.text((lx, y), f"+ {txt}", font=_font(15), fill=GREEN)
            if i < len(negatives):
                txt = negatives[i][:42] + "…" if len(negatives[i]) > 42 else negatives[i]
                draw.text((rx, y), f"- {txt}", font=_font(15), fill=RED)
            y += 26
        y += 10

    # ── Verdict ───────────────────────────────────────────────────────────────
    if verdict:
        draw.rectangle([80, y, W - 80, y + 1], fill=ACCENT2)
        y += 18
        draw.text((80, y), "VERDICT", font=_font(17, bold=True), fill=ACCENT)
        y += 28
        wrapped = textwrap.wrap(verdict, width=62)
        for line in wrapped[:3]:
            draw.text((80, y), line, font=_font(16), fill=GREY)
            y += 24

    # ── Футер ────────────────────────────────────────────────────────────────
    draw.rectangle([0, H - 60, W, H - 59], fill=ACCENT)
    draw.text((W // 2, H - 30), "LOOKSMAX BOT • @YourBotUsername",
              font=_font(18, bold=True), fill=GREY, anchor="mm")

    # ── Экспорт ───────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
