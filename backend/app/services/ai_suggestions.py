"""AI Suggestions service to generate exploratory topic suggestions for users.

Generates live, exploratory topic ideas using Anthropic Claude API based on a user's
interest tags, with a deterministic fallback handler if the LLM is unavailable.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.constants import INTEREST_TAXONOMY

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT_SECONDS: float = 15.0


def generate_fallback_ai_suggestions(interest_tags: List[str]) -> List[Dict[str, str]]:
    """Generate a deterministic list of 3 exploratory topic suggestions based on user interest tags.

    Args:
        interest_tags: List of interest tag strings for the user.

    Returns:
        List[Dict[str, str]]: Exactly 3 dicts with 'title', 'description', and 'related_tag'.
    """
    primary = interest_tags[0] if interest_tags else INTEREST_TAXONOMY[0]
    secondary = (
        interest_tags[1]
        if len(interest_tags) > 1
        else (interest_tags[0] if interest_tags else INTEREST_TAXONOMY[1])
    )
    tertiary = (
        interest_tags[2]
        if len(interest_tags) > 2
        else (interest_tags[0] if interest_tags else INTEREST_TAXONOMY[2])
    )

    return [
        {
            "title": f"Emerging Trends in {primary} Architecture",
            "description": f"Explore upcoming patterns, novel tools, and community discussions shaping modern {primary} projects.",
            "related_tag": primary,
        },
        {
            "title": f"Best Practices for {secondary} Integration",
            "description": f"Practical strategies and architectural blueprints for integrating {secondary} into scalable engineering workflows.",
            "related_tag": secondary,
        },
        {
            "title": f"Next-Generation {tertiary} Tooling & Insights",
            "description": f"A forward-looking exploration of upcoming open-source libraries and performance benchmarks in {tertiary}.",
            "related_tag": tertiary,
        },
    ]


def build_ai_suggestions_prompt(user_name: str, interest_tags: List[str]) -> str:
    """Construct prompt for Claude to generate 3 exploratory topic suggestions.

    Args:
        user_name: Display name of target user.
        interest_tags: List of interest tags for the user.

    Returns:
        str: Formatted user prompt string.
    """
    tags_str = ", ".join(interest_tags) if interest_tags else "general technology"
    taxonomy_str = ", ".join(INTEREST_TAXONOMY)
    return (
        f"You are an AI technical assistant generating exploratory content suggestions for {user_name}.\n"
        f"{user_name} is interested in the following topics: {tags_str}.\n\n"
        "Instructions:\n"
        "1. Generate EXACTLY 3 distinct, high-quality topic ideas that {user_name} might find interesting.\n"
        "2. Note: These are exploratory suggestions and topic concepts, NOT real published articles.\n"
        "3. For each suggestion, provide a concise 'title', a short 'description' (1-2 sentences), and a 'related_tag'.\n"
        f"4. The 'related_tag' field MUST be exactly one tag from this taxonomy list: {taxonomy_str}. Suggestions may explore tags slightly beyond the user's current interests, but related_tag must always be a valid taxonomy value.\n"
        "5. Return ONLY a valid JSON array of objects with keys 'title', 'description', and 'related_tag'. Do not include markdown codeblock wrappers, headers, or conversational text.\n"
        'Example format:\n[\n  {"title": "Topic Title 1", "description": "Short explanation 1.", "related_tag": "AI"},\n  {"title": "Topic Title 2", "description": "Short explanation 2.", "related_tag": "Cloud"},\n  {"title": "Topic Title 3", "description": "Short explanation 3.", "related_tag": "DevOps"}\n]'
    )


def call_llm_ai_suggestions(
    user_name: str,
    interest_tags: List[str],
    client: Optional[Any] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> List[Dict[str, str]]:
    """Execute API request to Groq LLM to generate exploratory suggestions.

    Args:
        user_name: Name of target user.
        interest_tags: List of interest tags.
        client: Optional injected Groq client or mock client.
        timeout: API call timeout in seconds.

    Returns:
        List[Dict[str, str]]: List of 3 suggestion dicts with 'title', 'description', and 'related_tag'.
    """
    prompt = build_ai_suggestions_prompt(user_name, interest_tags)

    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing or empty.")
        import groq

        client = groq.Groq(api_key=api_key, timeout=timeout)

    response = client.chat.completions.create(
        model=DEFAULT_GROQ_MODEL,
        max_tokens=400,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    if hasattr(response, "choices") and response.choices:
        first_choice = response.choices[0]
        text_content = ""
        if hasattr(first_choice, "message") and hasattr(first_choice.message, "content") and first_choice.message.content:
            text_content = first_choice.message.content.strip()
        elif isinstance(first_choice, dict) and "message" in first_choice:
            msg = first_choice["message"]
            if isinstance(msg, dict) and "content" in msg and msg["content"]:
                text_content = msg["content"].strip()

        # Clean JSON markdown fences if present
        if text_content.startswith("```"):
            lines = text_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_content = "\n".join(lines).strip()

        parsed = json.loads(text_content)
        if isinstance(parsed, list) and len(parsed) > 0:
            suggestions = []
            for item in parsed[:3]:
                if (
                    isinstance(item, dict)
                    and "title" in item
                    and "description" in item
                    and "related_tag" in item
                ):
                    tag = str(item["related_tag"]).strip()
                    if tag in INTEREST_TAXONOMY:
                        suggestions.append({
                            "title": str(item["title"]),
                            "description": str(item["description"]),
                            "related_tag": tag,
                        })
            if len(suggestions) == 3:
                return suggestions

    raise RuntimeError("Groq API response did not contain 3 valid suggestion objects with valid taxonomy related_tag.")


def generate_ai_suggestions(
    user_name: str,
    interest_tags: List[str],
    use_llm: bool = True,
    client: Optional[Any] = None,
) -> List[Dict[str, str]]:
    """Generate 3 exploratory topic suggestions for a user.

    Primary path calls Anthropic Claude API. Fallback path produces deterministic
    suggestions matching user's interest tags if LLM is disabled or fails.

    Args:
        user_name: Name of target user.
        interest_tags: List of interest tags for the user.
        use_llm: Whether to attempt LLM generation (default True).
        client: Optional injected client or mock client.

    Returns:
        List[Dict[str, str]]: 3 suggestion dicts containing 'title', 'description', and 'related_tag'.
    """
    if use_llm:
        try:
            suggestions = call_llm_ai_suggestions(
                user_name=user_name,
                interest_tags=interest_tags,
                client=client,
            )
            if suggestions and len(suggestions) == 3:
                return suggestions
        except Exception as exc:
            logger.warning(
                "LLM AI suggestions generation failed for user '%s': %s. Using fallback suggestions.",
                user_name,
                exc,
            )

    return generate_fallback_ai_suggestions(interest_tags)

