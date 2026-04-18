import json
import os

from openai import OpenAI

ACCOUNTABILITY_MODEL = os.environ.get("ACCOUNTABILITY_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

VALID_ALIGNMENTS = {"aligned", "partial", "diverged"}

SYSTEM_PROMPT = """You are a civic accountability analyst. You are given:
1. A government decision (what was decided).
2. The dominant themes from public comments submitted before the decision.
3. Optionally, a summary of the hearing.

Return a JSON object with exactly two keys:
- alignment: one of "aligned", "partial", or "diverged"
  - "aligned": the decision directly addresses the major concerns raised
  - "partial": the decision addresses some concerns but ignores others
  - "diverged": the decision contradicts or ignores the dominant public concerns
- reasoning: 2-4 sentences explaining why you chose this alignment label, citing specific cluster themes

Return ONLY valid JSON. No markdown, no explanation, no extra text."""


def compare_decision_to_clusters(
    decision_text: str, clusters: list[dict], summary: dict | None
) -> dict:
    """
    clusters: list of {name, description, comment_count}
    summary:  {issue_description, key_arguments, community_impact} or None
    returns:  {alignment: "aligned"|"partial"|"diverged", reasoning: str}
    """
    parts = [f"Government Decision:\n{decision_text}"]

    cluster_lines = []
    for c in clusters:
        line = f"- {c['name']} ({c.get('comment_count', 0)} comments): {c.get('description', '')}"
        cluster_lines.append(line)
    parts.append("Public Comment Themes:\n" + "\n".join(cluster_lines))

    if summary:
        summary_parts = []
        if summary.get("issue_description"):
            summary_parts.append(f"Issue: {summary['issue_description']}")
        if summary.get("key_arguments"):
            summary_parts.append(f"Key Arguments: {summary['key_arguments']}")
        if summary.get("community_impact"):
            summary_parts.append(f"Community Impact: {summary['community_impact']}")
        if summary_parts:
            parts.append("Hearing Summary:\n" + "\n".join(summary_parts))

    user_content = "\n\n".join(parts)

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    response = client.chat.completions.create(
        model=ACCOUNTABILITY_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content or ""

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"compare_decision_to_clusters: unparseable response: {raw!r}") from exc

    required = {"alignment", "reasoning"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"compare_decision_to_clusters: response missing keys {missing}: {raw!r}")

    if result["alignment"] not in VALID_ALIGNMENTS:
        raise ValueError(
            f"compare_decision_to_clusters: invalid alignment {result['alignment']!r}, "
            f"must be one of {VALID_ALIGNMENTS}"
        )

    return {"alignment": result["alignment"], "reasoning": result["reasoning"]}
