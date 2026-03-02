SYSTEM_PROMPT = """You are a recipe extraction engine.
Return valid JSON only. No markdown, no prose outside JSON.
Schema:
{
  "title": string,
  "description": string,
  "ingredients": string[],
  "steps": string[],
  "prep_time_minutes": number|null,
  "cook_time_minutes": number|null,
  "servings": number|null,
  "notes": string
}
If unknown, use null or empty values. Ensure ingredients and steps are arrays of concise strings.
"""


def build_user_prompt(transcript: str) -> str:
    return f"Create a normalized recipe JSON from this transcript:\n\n{transcript}"


def build_repair_prompt(bad_output: str) -> str:
    return (
        "Repair this into valid JSON matching the exact schema. Return JSON only.\n"
        f"Invalid content:\n{bad_output}"
    )
