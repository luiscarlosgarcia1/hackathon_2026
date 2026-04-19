import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a civic-affairs analyst. Given a legislative hearing, return a JSON object with exactly these four keys:
- issue_description: a concise 1-3 sentence description of the central issue being addressed
- stakeholders: a comma-separated list of key individuals, groups, or organizations involved
- key_arguments: a summary of the main arguments presented (2-4 sentences)
- community_impact: how this hearing outcome may affect the broader community (1-3 sentences)
Return ONLY valid JSON. No markdown, no explanation, no extra text."""


def summarize_hearing(hearing) -> dict:
    parts = [f"Title: {hearing.title}", f"Date: {hearing.date}"]
    if hearing.transcript:
        parts.append(f"Transcript:\n{hearing.transcript[:15000]}")
    if hearing.agenda:
        parts.append(f"Agenda:\n{hearing.agenda}")
    user_content = "\n\n".join(parts)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summarize_hearing: unparseable response: {raw!r}") from exc

    required = {"issue_description", "stakeholders", "key_arguments", "community_impact"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"summarize_hearing: response missing keys {missing}: {raw!r}")

    return {k: result[k] for k in required}

def extract_decision(hearing) -> str:
    parts = [f"Title: {hearing.title}", f"Date: {hearing.date}"]
    if hearing.transcript:
        parts.append(f"Transcript:\n{hearing.transcript[:15000]}")
    if hearing.summary:
        parts.append(f"Issue: {hearing.summary.issue_description}")
        parts.append(f"Key Arguments: {hearing.summary.key_arguments}")
        parts.append(f"Community Impact: {hearing.summary.community_impact}")
    user_content = "\n\n".join(parts)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a civic-affairs analyst. Based on the hearing title, date, and any available summary, write exactly 2 sentences describing what the government likely decided or what the outcome of this hearing was.
No markdown, no JSON, no extra text."""
            },
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()