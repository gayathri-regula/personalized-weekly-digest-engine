"""LLM summarization service with template-based fallback handler.

Converts top-ranked activity items into executive summary prose using the
Anthropic Claude API, with a robust Markdown template-based fallback if the API
is unavailable, unconfigured, or times out.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default Anthropic model per ARCHITECTURE.md Section 4.1
DEFAULT_CLAUDE_MODEL: str = "claude-sonnet-4-6"
DEFAULT_TIMEOUT_SECONDS: float = 15.0


def build_claude_prompt(
    user_name: str, ranked_items_with_details: List[Dict[str, Any]]
) -> str:
    """Construct a clear, focused prompt for Claude to generate digest prose.

    Args:
        user_name: Display name of the user receiving the digest.
        ranked_items_with_details: Joined list containing title, content,
            relevance_score, explanation_text, etc.

    Returns:
        str: Formatted user prompt string.
    """
    items_text_blocks = []
    for idx, item in enumerate(ranked_items_with_details, start=1):
        title = item.get("title", "Untitled")
        explanation = item.get("explanation_text", "relevant update")
        score = item.get("relevance_score", 0.0)
        content = item.get("content", "")
        snippet = content[:150].strip() + ("..." if len(content) > 150 else "")

        items_text_blocks.append(
            f"{idx}. Title: {title}\n"
            f"   Explanation: {explanation}\n"
            f"   Relevance Score: {score:.2f}\n"
            f"   Snippet: {snippet}"
        )

    joined_items = "\n\n".join(items_text_blocks)

    return (
        f"You are crafting a personalized, high-value weekly digest executive summary for {user_name}.\n"
        f"Here are the top-ranked activity items curated specifically for {user_name} this week:\n\n"
        f"{joined_items}\n\n"
        "Instructions & Phrasing Guidance:\n"
        f"1. Executive Summary Quality: Compose a fluid, articulate, 2-4 sentence executive summary synthesized specifically for {user_name}.\n"
        "2. Dynamic & Varied Phrasing: Vary your opening hooks, transitional phrasing, and synthesis structure across calls (e.g., framing around emerging architectural trends, key technical takeaways, strategic industry shifts, or actionable engineering highlights). Avoid repetitive formulaic templates.\n"
        "3. Strict Grounding: Base all insights strictly on the provided item titles, snippets, and match explanations ('explanation_text'). Do NOT invent, assume, or hallucinate external facts, items, or scores.\n"
        "4. Truthful Relevance: Seamlessly connect the highlighted topics to the matching user interests indicated in the explanation texts (e.g., 'because you follow ...').\n"
        "5. Output Format: Output ONLY the final executive summary paragraph without any markdown headings, bulleted lists, intro preambles, or conversational sign-offs."
    )


def generate_template_fallback_summary(
    user_name: str, ranked_items_with_details: List[Dict[str, Any]]
) -> str:
    """Generate a deterministic Markdown template summary when LLM is disabled or fails.

    Args:
        user_name: Name of the user receiving the digest.
        ranked_items_with_details: List of top ranked items with full details.

    Returns:
        str: Formatted Markdown summary string.
    """
    if not ranked_items_with_details:
        return "No highly relevant updates were found for you this week."

    lines = [f"### Weekly Digest Summary for {user_name}\n"]
    for item in ranked_items_with_details:
        try:
            title = item.get("title", "Untitled Update")
            explanation = item.get("explanation_text", "recommended item")
            content = item.get("content", "")
            snippet = content[:120].strip() + ("..." if len(content) > 120 else "")
            lines.append(f"- **{title}** — *{explanation}*: {snippet}")
        except Exception as err:
            logger.warning("Error formatting item in fallback summary: %s", err)
            continue

    return "\n".join(lines)


def call_llm_summarizer(
    user_name: str,
    ranked_items_with_details: List[Dict[str, Any]],
    client: Optional[Any] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Execute API request to Anthropic Claude to generate digest summary prose.

    Args:
        user_name: Name of the target user.
        ranked_items_with_details: Joined list of items with details.
        client: Optional injected Anthropic client or mock client for testing.
        timeout: API call timeout in seconds.

    Returns:
        str: Generated summary prose text.

    Raises:
        ValueError, RuntimeError, Exception: On API errors, auth failures, or timeouts.
    """
    prompt = build_claude_prompt(user_name, ranked_items_with_details)

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is missing or empty."
            )
        import anthropic

        client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    # Call messages API
    response = client.messages.create(
        model=DEFAULT_CLAUDE_MODEL,
        max_tokens=300,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract response content text
    if hasattr(response, "content") and response.content:
        first_block = response.content[0]
        if hasattr(first_block, "text"):
            return first_block.text.strip()
        elif isinstance(first_block, dict) and "text" in first_block:
            return first_block["text"].strip()

    raise RuntimeError("Unexpected response structure from Anthropic API.")


def generate_digest_summary(
    user_name: str,
    ranked_items_with_details: List[Dict[str, Any]],
    use_llm: bool = True,
    client: Optional[Any] = None,
) -> str:
    """Generate a digest summary prose string for a user's top-ranked items.

    Primary path uses Anthropic Claude LLM. Fallback path produces structured Markdown
    if use_llm is False or if any LLM API error occurs.

    Args:
        user_name: Name of the target user.
        ranked_items_with_details: List of top ranked items joined with titles/content.
        use_llm: Whether to attempt LLM generation (default True).
        client: Optional injected Anthropic client or mock client.

    Returns:
        str: Executive summary prose or template markdown summary.
    """
    # Empty items edge case (ARCHITECTURE.md Section 10.1)
    if not ranked_items_with_details:
        return "No highly relevant updates were found for you this week."

    if use_llm:
        try:
            summary_prose = call_llm_summarizer(
                user_name=user_name,
                ranked_items_with_details=ranked_items_with_details,
                client=client,
            )
            if summary_prose:
                return summary_prose
        except Exception as exc:
            logger.warning(
                "LLM summarizer failed for user '%s': %s. Falling back to template summary.",
                user_name,
                exc,
            )

    # Fallback path (ARCHITECTURE.md Section 4.2 & 10.3)
    return generate_template_fallback_summary(user_name, ranked_items_with_details)
