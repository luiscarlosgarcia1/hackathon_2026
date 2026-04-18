import json
import os

from openai import OpenAI

CLUSTERING_MODEL = os.environ.get("CLUSTERING_MODEL", os.environ.get("SUMMARIZATION_MODEL", "llama3.2"))
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

SYSTEM_PROMPT = """You are a civic-affairs analyst. Given a list of public comments (each with an id and body), group them into thematic clusters.

Return ONLY a valid JSON array. Each element must have exactly these keys:
- name: a short theme label (e.g. "Affordability", "Traffic Safety")
- description: a 1-2 sentence summary of what comments in this cluster share
- comment_ids: an array of integer IDs belonging to this cluster

Rules:
- Every comment ID from the input must appear in exactly one cluster.
- Do not invent IDs or omit any.
- Return ONLY the JSON array. No markdown, no explanation, no extra text."""


def cluster_comments(comments: list) -> list[dict]:
    if len(comments) < 2:
        raise ValueError("need at least 2 comments to cluster")

    user_content = json.dumps(comments, ensure_ascii=False)

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    response = client.chat.completions.create(
        model=CLUSTERING_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content or ""

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"cluster_comments: unparseable response: {raw!r}") from exc

    if not isinstance(result, list):
        raise ValueError(f"cluster_comments: expected a JSON array, got: {raw!r}")

    input_ids = {c["id"] for c in comments}
    assigned_ids: set[int] = set()

    for cluster in result:
        for key in ("name", "description", "comment_ids"):
            if key not in cluster:
                raise ValueError(f"cluster_comments: cluster missing key '{key}': {cluster!r}")
        for cid in cluster["comment_ids"]:
            if cid in assigned_ids:
                raise ValueError(f"cluster_comments: comment id {cid} appears in multiple clusters")
            assigned_ids.add(cid)

    missing = input_ids - assigned_ids
    if missing:
        raise ValueError(f"cluster_comments: input IDs missing from output: {missing}")

    return result
