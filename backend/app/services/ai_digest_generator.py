"""AI Digest Generator service for producing tailored, fictional activity items.

Generates 5 synthetic/fictional activity items tailored to a user's interest tags using
the Anthropic Claude API, with a deterministic fallback template generator if the API
is unavailable, unconfigured, or fails.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.constants import INTEREST_TAXONOMY
from app.utils import get_reference_now

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_MODEL: str = "claude-sonnet-4-6"
DEFAULT_TIMEOUT_SECONDS: float = 15.0

FALLBACK_ITEM_TEMPLATES: Dict[str, Dict[str, str]] = {
    "AI": {
        "title": "Architecting Autonomous Agent Systems with Deterministic Guardrails",
        "content": "Explore modern patterns for building reliable multi-agent workflows, combining state machine routing with LLM reasoning pipelines.",
    },
    "Machine Learning": {
        "title": "Optimizing Model Inference Latency via Quantization & Pruning",
        "content": "A comprehensive benchmark comparing FP16, INT8, and INT4 quantization strategies for low-latency production deployments.",
    },
    "Python": {
        "title": "High-Performance Asynchronous Microservices with FastAPI & AsyncIO",
        "content": "Practical strategies for managing connection pools, concurrency limits, and async ORM pipelines under heavy throughput.",
    },
    "JavaScript": {
        "title": "Mastering Server Components & Modern React Rendering Pipelines",
        "content": "Deep dive into server-driven UI architecture, streaming SSR, and zero-bundle-size client components.",
    },
    "Cloud": {
        "title": "Multi-Region Cloud Resilience & Automated Disaster Recovery Blueprints",
        "content": "Best practices for implementing active-active database replication and automated failover across cloud regions.",
    },
    "DevOps": {
        "title": "GitOps Infrastructure Management with Automated Drift Detection",
        "content": "Streamlining Kubernetes cluster deployments and infrastructure provisioning using declarative GitOps pipelines.",
    },
    "Data Science": {
        "title": "Real-Time Feature Engineering Pipelines for Production ML Systems",
        "content": "Building scalable feature stores to synchronize offline training data with online real-time inference tables.",
    },
    "Mobile Development": {
        "title": "Cross-Platform Performance Optimization & Native Bridge Benchmarks",
        "content": "Evaluating memory footprints, render performance, and native module bindings across modern mobile frameworks.",
    },
    "Security": {
        "title": "Zero-Trust API Security Architecture & OAuth2 Hardening Guide",
        "content": "Implementing fine-grained authorization policies, token introspection, and proactive threat detection for microservices.",
    },
    "UI/UX Design": {
        "title": "Designing Accessible & Micro-Animated Component Libraries",
        "content": "Key design tokens, contrast compliance standards, and fluid motion guidelines for modern web design systems.",
    },
    "Backend Engineering": {
        "title": "Event-Driven Microservices Architecture & Message Bus Patterns",
        "content": "Designing resilient pub/sub event streams, idempotent consumer handlers, and dead-letter queue recovery mechanisms.",
    },
    "Open Source": {
        "title": "Building Sustainable Open-Source Community Tooling & Governance",
        "content": "Insights into maintainer workflows, release automation, and collaborative governance models for open projects.",
    },
}


def generate_fallback_ai_digest_items(
    user_name: str, interest_tags: List[str]
) -> List[Dict[str, Any]]:
    """Generate 5 deterministic, realistic fallback activity items based on user interest tags.

    Args:
        user_name: Display name of the target user.
        interest_tags: List of interest tags specified by the user.

    Returns:
        List[Dict[str, Any]]: List of 5 dicts ready for ActivityItem and DigestItem creation.
    """
    effective_tags = interest_tags if interest_tags else INTEREST_TAXONOMY[:3]
    num_tags = len(effective_tags)
    ref_now = get_reference_now()

    # Pre-calculated synthetic relevance scores for 5 items
    synthetic_scores = [0.95, 0.92, 0.89, 0.86, 0.83]

    items: List[Dict[str, Any]] = []
    for idx in range(5):
        tag = effective_tags[idx % num_tags]
        template = FALLBACK_ITEM_TEMPLATES.get(
            tag,
            {
                "title": f"Emerging Innovations & Architecture Patterns in {tag}",
                "content": f"An actionable technical breakdown of modern design patterns, toolchains, and community insights in {tag}.",
            },
        )

        items.append(
            {
                "title": template["title"],
                "content": template["content"],
                "category_tags": [tag],
                "explanation_text": f"AI-generated highlight tailored to your interest in {tag}",
                "relevance_score": synthetic_scores[idx],
                "rank_position": idx + 1,
                "created_at": ref_now,
                "engagement_metadata": {
                    "views": 120 - idx * 10,
                    "likes": 25 - idx * 2,
                    "shares": 6 - idx,
                    "is_ai_generated": True,
                },
            }
        )

    return items


def build_ai_digest_prompt(user_name: str, interest_tags: List[str]) -> str:
    """Construct prompt for Claude to generate 5 fictional activity updates.

    Args:
        user_name: Name of target user.
        interest_tags: List of interest tags specified by user.

    Returns:
        str: Formatted prompt string for Claude API.
    """
    tags_str = ", ".join(interest_tags) if interest_tags else "general technology"
    taxonomy_str = ", ".join(INTEREST_TAXONOMY)

    return (
        f"You are an AI engineering assistant generating personalized technical activity updates for {user_name}.\n"
        f"{user_name} follows the following interest topics: {tags_str}.\n\n"
        "Instructions:\n"
        "1. Generate EXACTLY 5 distinct, high-quality fictional activity updates tailored to {user_name}'s topics.\n"
        "2. Distribute topics evenly across {user_name}'s interest tags.\n"
        "3. For each item, provide:\n"
        "   - 'title': A compelling, professional technical title.\n"
        "   - 'content': A detailed 2-3 sentence technical description or breakdown.\n"
        f"   - 'category_tags': A JSON array containing 1-2 tags. ALL tags MUST be chosen strictly from this allowed taxonomy: {taxonomy_str}.\n"
        "   - 'explanation_text': A short explanation phrase explaining why this item was generated for {user_name} (e.g. 'AI-generated highlight tailored to your interest in AI').\n"
        "4. Return ONLY a valid JSON array of 5 objects. Do not include markdown codeblock wrappers, preambles, or conversational sign-offs.\n"
        'Example format:\n[\n  {"title": "Title 1", "content": "Content 1.", "category_tags": ["AI"], "explanation_text": "AI-generated highlight tailored to your interest in AI"}\n]'
    )


def call_llm_ai_digest_generator(
    user_name: str,
    interest_tags: List[str],
    client: Optional[Any] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> List[Dict[str, Any]]:
    """Execute API request to Anthropic Claude to generate 5 fictional activity items.

    Args:
        user_name: Name of target user.
        interest_tags: List of interest tags.
        client: Optional injected Anthropic client or mock client.
        timeout: API call timeout in seconds.

    Returns:
        List[Dict[str, Any]]: List of 5 parsed and formatted activity item dicts.

    Raises:
        ValueError, RuntimeError, Exception: On API errors, auth failures, or unparseable output.
    """
    prompt = build_ai_digest_prompt(user_name, interest_tags)

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is missing or empty."
            )
        import anthropic

        client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    response = client.messages.create(
        model=DEFAULT_CLAUDE_MODEL,
        max_tokens=1000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    if hasattr(response, "content") and response.content:
        first_block = response.content[0]
        text_content = ""
        if hasattr(first_block, "text"):
            text_content = first_block.text.strip()
        elif isinstance(first_block, dict) and "text" in first_block:
            text_content = first_block["text"].strip()

        # Clean JSON markdown fences if present
        if text_content.startswith("```"):
            lines = text_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_content = "\n".join(lines).strip()

        parsed = json.loads(text_content)
        if isinstance(parsed, list) and len(parsed) >= 5:
            ref_now = get_reference_now()
            synthetic_scores = [0.95, 0.92, 0.89, 0.86, 0.83]
            taxonomy_set = set(INTEREST_TAXONOMY)
            fallback_primary_tag = interest_tags[0] if interest_tags else INTEREST_TAXONOMY[0]

            results = []
            for idx, raw in enumerate(parsed[:5], start=1):
                raw_tags = raw.get("category_tags", [])
                valid_tags = [t for t in raw_tags if t in taxonomy_set]
                if not valid_tags:
                    valid_tags = [fallback_primary_tag]

                results.append(
                    {
                        "title": str(raw.get("title", f"AI Highlight #{idx}")),
                        "content": str(raw.get("content", "")),
                        "category_tags": valid_tags,
                        "explanation_text": str(
                            raw.get(
                                "explanation_text",
                                f"AI-generated highlight tailored to your interest in {valid_tags[0]}",
                            )
                        ),
                        "relevance_score": synthetic_scores[idx - 1],
                        "rank_position": idx,
                        "created_at": ref_now,
                        "engagement_metadata": {
                            "views": 150 - idx * 15,
                            "likes": 30 - idx * 3,
                            "shares": 8 - idx,
                            "is_ai_generated": True,
                        },
                    }
                )
            return results

    raise RuntimeError("Claude API response did not contain 5 valid generated item objects.")


def generate_ai_digest_items(
    user_name: str,
    interest_tags: List[str],
    use_llm: bool = True,
    client: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Generate 5 AI activity items for a user's digest.

    Primary path calls Anthropic Claude API. Fallback path produces deterministic
    synthetic activity items if LLM is disabled or fails.

    Args:
        user_name: Display name of target user.
        interest_tags: List of interest tags specified by user.
        use_llm: Whether to attempt LLM generation (default True).
        client: Optional injected client or mock client.

    Returns:
        List[Dict[str, Any]]: List of 5 generated item dictionaries.
    """
    if use_llm:
        try:
            items = call_llm_ai_digest_generator(
                user_name=user_name,
                interest_tags=interest_tags,
                client=client,
            )
            if items and len(items) == 5:
                return items
        except Exception as exc:
            logger.warning(
                "LLM AI digest generation failed for user '%s': %s. Using synthetic fallback items.",
                user_name,
                exc,
            )

    return generate_fallback_ai_digest_items(user_name, interest_tags)
