import json
import os

from openai import OpenAI

SUMMARIZATION_MODEL = os.environ.get("SUMMARIZATION_MODEL", "codex-mini-latest")

SYSTEM_PROMPT = """You are a civic-affairs analyst. Given a legislative hearing, return a JSON object with exactly these four keys:
- issue_description: a concise 1-3 sentence description of the central issue being addressed
- stakeholders: a comma-separated list of key individuals, groups, or organizations involved
- key_arguments: a summary of the main arguments presented (2-4 sentences)
- community_impact: how this hearing outcome may affect the broader community (1-3 sentences)

Return ONLY valid JSON. No markdown, no explanation, no extra text."""


def summarize_hearing(hearing) -> dict:
    parts = [f"Title: {hearing.title}", f"Date: {hearing.date}"]
    if hearing.transcript:
        parts.append(f"Transcript:\n{hearing.transcript}")
    if hearing.agenda:
        parts.append(f"Agenda:\n{hearing.agenda}")

    user_content = "\n\n".join(parts)

    client = OpenAI()
    response = client.chat.completions.create(
        model=SUMMARIZATION_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content or ""

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summarize_hearing: unparseable response: {raw!r}") from exc

    required = {"issue_description", "stakeholders", "key_arguments", "community_impact"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"summarize_hearing: response missing keys {missing}: {raw!r}")

    return {k: result[k] for k in required}
