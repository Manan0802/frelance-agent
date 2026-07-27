import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_json(raw: str, default: dict) -> dict:
    """Extract a JSON object from an LLM response.

    Models routinely wrap JSON in ```json fences or top-and-tail it with prose;
    a bare json.loads() raises on both. Callers previously swallowed that into a
    fallback, silently losing the payload — empty pain_points, or a score of 0
    that auto-rejected the job.
    """
    if not raw:
        return default

    candidates = [raw.strip()]
    fenced = _FENCE.search(raw)
    if fenced:
        candidates.append(fenced.group(1))
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        candidates.append(raw[start:end + 1])

    for c in candidates:
        try:
            # strict=False: models format long values as multi-line lists, which
            # puts literal newlines inside JSON strings. That's invalid JSON and
            # the default parser rejects the whole object over it.
            parsed = json.loads(c, strict=False)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return default
