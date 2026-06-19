import asyncio
import base64
import httpx
from config import OPENAI_API_KEY

# ── Первый проход: визуальный анализ лица ────────────────────────────────────
ANALYSIS_PROMPT = """\
You are a professional facial analyst specializing in looksmaxxing assessment. \
You have studied thousands of faces and understand bone structure, soft tissue, \
and facial harmony at an expert level.

Carefully examine this photo and analyze the face with precision. \
Look at actual bone structure, not just the photo angle or lighting.

Respond STRICTLY in this exact format — no intro, no extra text:

SCORE: [X.X/10]
TIER: [NPC / Below Average / Average / Above Average / Attractive / Chad / Gigachad]

BREAKDOWN:
• Jawline & Chin: [X.X/10] — [specific observation about their actual jaw shape, angle, projection]
• Cheekbones: [X.X/10] — [specific observation about zygomatic prominence and width]
• Eyes & Canthal Tilt: [X.X/10] — [note tilt direction, eye shape, orbital bone, limbal rings if visible]
• Nose: [X.X/10] — [bridge width, tip projection, nostril width relative to face]
• Lips & Philtrum: [X.X/10] — [lip ratio, philtrum length, vermillion border definition]
• Skin Quality: [X.X/10] — [texture, clarity, any notable features]
• Facial Harmony: [X.X/10] — [how well all features work together, facial thirds balance]

POSITIVES:
+ [specific strong feature with why it adds value]
+ [specific strong feature]
+ [specific strong feature]

NEGATIVES:
- [specific weak feature — score impact in brackets e.g. (-0.8)]
- [specific weak feature — score impact]
- [specific weak feature — score impact, or write "none" if genuinely none]

VERDICT: [2 sentences — brutally honest but not cruel, use looksmaxxing terminology naturally]

Scoring guide:
1-3: Significant disadvantages
4-5: Below average to average
5-6: Average
6-7: Above average, attractive
7-8: Very attractive
8-9: Exceptional
9-10: Top 1%
Be precise — avoid generic 7/10 ratings. Most people fall 4.5–6.5."""

# ── Второй проход: персонализированные советы на основе первого анализа ──────
ADVICE_PROMPT_TEMPLATE = """\
You are a looksmaxxing coach. Based on this facial analysis:

{analysis}

Now look at the photo again and give highly specific, actionable looksmaxxing advice \
tailored EXACTLY to what you see on this person's face. \
Do NOT give generic tips — every tip must reference their specific features from the analysis above.

Respond STRICTLY in this format:

LOOKSMAX ROADMAP:

🔴 HIGH IMPACT (do these first):
1. [specific tip referencing their actual features — explain why for THIS person]
2. [specific tip]

🟡 MEDIUM IMPACT:
3. [specific tip]
4. [specific tip]

🟢 QUICK WINS (easy changes, visible results fast):
5. [specific tip]
6. [specific tip]

POTENTIAL UNLOCKED: [X.X/10] — [what their score could realistically reach with full looksmaxxing]

ROLE MODEL: [name 1-2 celebrities or public figures with similar facial structure they could study]"""

# ── Детальный второй проход (платный) ────────────────────────────────────────
DETAILED_ADVICE_TEMPLATE = """\
You are an expert looksmaxxing analyst with knowledge of facial surgery, \
dermatology, and aesthetic medicine. Based on this facial analysis:

{analysis}

Examine the photo carefully and provide a comprehensive advanced assessment.

Respond STRICTLY in this format:

ADVANCED METRICS:
• Facial thirds balance: [upper/middle/lower — which is dominant and what it means]
• fWHR (facial width-to-height ratio): [estimate and what it signals]
• Symmetry: [X.X/10] — [what's asymmetric and how noticeable]
• Eye type: [hunter/neutral/prey] — [canthal tilt angle assessment]
• Gonial angle: [sharp/medium/obtuse] — [what it means for jaw appearance]
• Maxillary projection: [good/average/recessed] — [how it affects midface]

LOOKSMAX ROADMAP:

🔴 HIGH IMPACT (do these first):
1. [tip specific to their features — reference actual analysis]
2. [tip]
3. [tip]

🟡 MEDIUM IMPACT:
4. [tip]
5. [tip]

🟢 QUICK WINS:
6. [tip]
7. [tip]

💊 ADVANCED OPTIONS (if serious about maxing):
• [mewing/bone smashing/surgery consideration relevant to their specific structure]
• [another advanced option]

POTENTIAL UNLOCKED: [X.X/10] — [realistic ceiling with full looksmaxxing commitment]
ROLE MODEL: [1-2 celebrities with similar bone structure to study]
HONEST TAKE: [1-2 sentences — what will make the biggest real difference for THIS person]"""


async def _call_gpt(
    client: httpx.AsyncClient,
    messages: list,
    max_tokens: int = 900,
) -> str:
    payload = {
        "model": "gpt-4o",
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": 0.4,  # низкая температура = стабильнее, точнее
    }
    response = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def analyze_face(image_bytes: bytes, detailed: bool = False) -> tuple[str, str]:
    """
    Returns (analysis, advice) — два отдельных блока текста.
    Первый проход: анализ лица.
    Второй проход: персонализированные советы на основе первого.
    """
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_content = {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{image_b64}",
            "detail": "high",
        },
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        # Первый проход — анализ
        analysis = await _call_gpt(
            client,
            messages=[{
                "role": "user",
                "content": [image_content, {"type": "text", "text": ANALYSIS_PROMPT}],
            }],
            max_tokens=900,
        )

        # Второй проход — советы, передаём фото + результат первого прохода
        advice_prompt = (
            DETAILED_ADVICE_TEMPLATE if detailed else ADVICE_PROMPT_TEMPLATE
        ).format(analysis=analysis)

        advice = await _call_gpt(
            client,
            messages=[
                {
                    "role": "user",
                    "content": [image_content, {"type": "text", "text": ANALYSIS_PROMPT}],
                },
                {
                    "role": "assistant",
                    "content": analysis,
                },
                {
                    "role": "user",
                    "content": [image_content, {"type": "text", "text": advice_prompt}],
                },
            ],
            max_tokens=1100 if detailed else 900,
        )

    return analysis, advice
