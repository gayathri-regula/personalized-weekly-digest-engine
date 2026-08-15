"""AI Digest Generator service for producing tailored, fictional activity items.

Generates 5 synthetic/fictional activity items tailored to a user's interest tags
and exploratory topics using the Anthropic Claude API, with a fallback template generator
if the API is unavailable, unconfigured, or fails.
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

# Exploratory topics for fallback generation outside standard taxonomy tags
EXPLORATORY_FALLBACK_TOPICS = [
    {
        "tag": "Quantum Computing",
        "section": "Quantum & Hardware Acceleration",
        "title": "Architecting Fault-Tolerant Quantum Algorithms with Surface Codes",
        "content": "A deep dive into quantum error correction, logical qubit mapping, and hybrid classical-quantum solver integration.",
        "explanation": "Exploratory update: Emerging breakthroughs in Quantum Computing",
    },
    {
        "tag": "Edge AI",
        "section": "Edge & Autonomous Systems",
        "title": "On-Device Neural Network Pruning for Low-Power Microcontrollers",
        "content": "Exploring post-training quantization, sparse matrix arithmetic, and real-time vision processing on low-wattage hardware.",
        "explanation": "Exploratory update: Innovative developments in Edge AI",
    },
    {
        "tag": "Compiler Design",
        "section": "Systems Programming & Compilers",
        "title": "MLIR Pipeline Optimization for Custom Domain-Specific Accelerators",
        "content": "Designing multi-level intermediate representation lowering passes for specialized AI hardware architectures.",
        "explanation": "Exploratory update: Emerging patterns in System Compiler Design",
    },
    {
        "tag": "Vector Databases",
        "section": "Distributed Storage & Indexing",
        "title": "High-Throughput HNSW Graph Indexing for Billion-Scale Similarity Search",
        "content": "Benchmarking memory layout strategies, SIMD vectorization, and dynamic graph partitioning in real-time vector search.",
        "explanation": "Exploratory update: Emerging trends in Vector Storage Engines",
    },
]

# Complete 3-variant fallback item template library per taxonomy tag
FALLBACK_ITEM_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "AI": [
        {
            "title": "Architecting Autonomous Agent Systems with Deterministic Guardrails",
            "content": "Explore modern patterns for building reliable multi-agent workflows, combining state machine routing with LLM reasoning pipelines.",
            "section": "AI & Autonomous Systems",
        },
        {
            "title": "Scaling LLM Inference Infrastructure with Speculative Decoding",
            "content": "A technical guide to optimizing auto-regressive model throughput using draft models and parallel token verification.",
            "section": "AI & Autonomous Systems",
        },
        {
            "title": "Retrieval-Augmented Generation at Scale: Vector Indexing & Reranking",
            "content": "Deep dive into hybrid search strategies, dense embeddings, and cross-encoder reranking for production knowledge bases.",
            "section": "AI & Autonomous Systems",
        },
    ],
    "Machine Learning": [
        {
            "title": "Optimizing Model Inference Latency via Quantization & Pruning",
            "content": "A comprehensive benchmark comparing FP16, INT8, and INT4 quantization strategies for low-latency production deployments.",
            "section": "Machine Learning & MLOps",
        },
        {
            "title": "Distributed Training Strategies for Large-Scale Deep Learning Models",
            "content": "Analyzing data parallelism, pipeline parallelism, and DeepSpeed ZeRO memory optimization strategies across GPU clusters.",
            "section": "Machine Learning & MLOps",
        },
        {
            "title": "Continuous Model Monitoring & Automated Drift Detection in MLOps",
            "content": "Best practices for tracking feature store drift, concept drift, and performance degradation in live prediction services.",
            "section": "Machine Learning & MLOps",
        },
    ],
    "Python": [
        {
            "title": "High-Performance Asynchronous Microservices with FastAPI & AsyncIO",
            "content": "Practical strategies for managing connection pools, concurrency limits, and async ORM pipelines under heavy throughput.",
            "section": "Languages & Ecosystems",
        },
        {
            "title": "Advanced Memory Management & Garbage Collection in Python 3.12+",
            "content": "Understanding reference counting, cyclic GC tweaks, and object layout optimizations for memory-intensive applications.",
            "section": "Languages & Ecosystems",
        },
        {
            "title": "Modern Python Packaging & Dependency Resolution with UV & Hatch",
            "content": "Streamlining build pipelines, lockfile generation, and virtual environment isolation in enterprise Python codebases.",
            "section": "Languages & Ecosystems",
        },
    ],
    "JavaScript": [
        {
            "title": "Mastering Server Components & Modern React Rendering Pipelines",
            "content": "Deep dive into server-driven UI architecture, streaming SSR, and zero-bundle-size client components.",
            "section": "Languages & Ecosystems",
        },
        {
            "title": "Optimizing Web Vitals & Hydration Performance in Next.js Apps",
            "content": "Tactics for reducing main-thread block time, deferring non-critical scripts, and eliminating layout shifts in complex UI.",
            "section": "Languages & Ecosystems",
        },
        {
            "title": "Event-Driven Node.js Architecture & Worker Thread Concurrency",
            "content": "Leveraging event loops, libuv worker pools, and shared memory buffers for CPU-intensive JavaScript tasks.",
            "section": "Languages & Ecosystems",
        },
    ],
    "Cloud": [
        {
            "title": "Multi-Region Cloud Resilience & Automated Disaster Recovery Blueprints",
            "content": "Best practices for implementing active-active database replication and automated failover across cloud regions.",
            "section": "Cloud & DevOps",
        },
        {
            "title": "Serverless Architecture Optimization & Cold Start Reduction Techniques",
            "content": "Strategies for fine-tuning provisioned concurrency, memory allocation, and lightweight runtimes in serverless environments.",
            "section": "Cloud & DevOps",
        },
        {
            "title": "Zero-Trust Infrastructure Provisioning with Terraform & OpenTofu",
            "content": "Managing immutable infrastructure, state file security, and modular policy-as-code enforcement in multi-cloud setups.",
            "section": "Cloud & DevOps",
        },
    ],
    "DevOps": [
        {
            "title": "GitOps Infrastructure Management with Automated Drift Detection",
            "content": "Streamlining Kubernetes cluster deployments and infrastructure provisioning using declarative GitOps pipelines.",
            "section": "Cloud & DevOps",
        },
        {
            "title": "Zero-Downtime Deployment Strategies with Canary & Blue-Green Rollouts",
            "content": "Implementing automated health checks, progressive traffic splitting, and instant rollback mechanisms in CI/CD pipelines.",
            "section": "Cloud & DevOps",
        },
        {
            "title": "Comprehensive Container Security & Image Vulnerability Scanning",
            "content": "Hardening Dockerfiles, enforcing non-root runtime environments, and automating container security gates in build pipelines.",
            "section": "Cloud & DevOps",
        },
    ],
    "Data Science": [
        {
            "title": "Real-Time Feature Engineering Pipelines for Production ML Systems",
            "content": "Building scalable feature stores to synchronize offline training data with online real-time inference tables.",
            "section": "Data Science & Analytics",
        },
        {
            "title": "Scalable Analytical Query Engine Design with Apache Arrow & Polars",
            "content": "Leveraging columnar memory formats, zero-copy serialization, and multi-core parallelism for massive datasets.",
            "section": "Data Science & Analytics",
        },
        {
            "title": "Automated Data Quality Validation & Anomaly Detection Frameworks",
            "content": "Enforcing schema contracts, statistical distribution checks, and automated alerting across distributed data pipelines.",
            "section": "Data Science & Analytics",
        },
    ],
    "Mobile Development": [
        {
            "title": "Cross-Platform Performance Optimization & Native Bridge Benchmarks",
            "content": "Evaluating memory footprints, render performance, and native module bindings across modern mobile frameworks.",
            "section": "Frontend & Mobile",
        },
        {
            "title": "Offline-First Mobile Synchronization Architecture with Local Databases",
            "content": "Designing conflict-free replicated data types (CRDTs) and background sync workers for resilient mobile UX.",
            "section": "Frontend & Mobile",
        },
        {
            "title": "Mobile App Battery & CPU Profiling for High-Frequency Render Loops",
            "content": "Identifying thread starvation, unneeded layout passes, and resource leaks using native mobile diagnostic tools.",
            "section": "Frontend & Mobile",
        },
    ],
    "Security": [
        {
            "title": "Zero-Trust API Security Architecture & OAuth2 Hardening Guide",
            "content": "Implementing fine-grained authorization policies, token introspection, and proactive threat detection for microservices.",
            "section": "Security & Infrastructure",
        },
        {
            "title": "Automated Software Supply Chain Security & Dependency Attestation",
            "content": "Securing build artifact provenance, generating SBOMs, and preventing dependency confusion attacks.",
            "section": "Security & Infrastructure",
        },
        {
            "title": "Application-Layer Encryption & Key Rotation Best Practices",
            "content": "Implementing envelope encryption, HSM key management, and zero-downtime cryptographic key rotation schemas.",
            "section": "Security & Infrastructure",
        },
    ],
    "UI/UX Design": [
        {
            "title": "Designing Accessible & Micro-Animated Component Libraries",
            "content": "Key design tokens, contrast compliance standards, and fluid motion guidelines for modern web design systems.",
            "section": "Frontend & Mobile",
        },
        {
            "title": "Design System Token Management & Cross-Platform Synchronization",
            "content": "Automating design token propagation from Figma styles to web, iOS, and Android theme configurations.",
            "section": "Frontend & Mobile",
        },
        {
            "title": "User Cognitive Load Reduction & Micro-Interaction Design Patterns",
            "content": "Crafting progressive disclosure interfaces, contextual feedback, and intuitive navigation structures.",
            "section": "Frontend & Mobile",
        },
    ],
    "Backend Engineering": [
        {
            "title": "Event-Driven Microservices Architecture & Message Bus Patterns",
            "content": "Designing resilient pub/sub event streams, idempotent consumer handlers, and dead-letter queue recovery mechanisms.",
            "section": "Backend Engineering",
        },
        {
            "title": "High-Throughput Database Partitioning & Sharding Strategies",
            "content": "Optimizing database schemas for horizontal scaling, distributed transactions, and query routing across shards.",
            "section": "Backend Engineering",
        },
        {
            "title": "API Gateway Rate Limiting & Distributed Throttling Architectures",
            "content": "Implementing token bucket algorithms, Redis-backed sliding windows, and graceful client degradation during load spikes.",
            "section": "Backend Engineering",
        },
    ],
    "Open Source": [
        {
            "title": "Building Sustainable Open-Source Community Tooling & Governance",
            "content": "Insights into maintainer workflows, release automation, and collaborative governance models for open projects.",
            "section": "Open Source & Community",
        },
        {
            "title": "Optimizing Monorepo Developer Experience & Incremental Build Caching",
            "content": "Leveraging remote build caches, dependency graph pruning, and automated change-impact analysis in open codebases.",
            "section": "Open Source & Community",
        },
        {
            "title": "Open Source Compliance & License Compatibility Management",
            "content": "Navigating permissiveness, copyleft obligations, and automated license scanning in open-source distributions.",
            "section": "Open Source & Community",
        },
    ],
}


def sanitize_category_tags(raw_tags: Any, fallback_tag: str = "Technology") -> List[str]:
    """Sanitize open-ended category tags returned by LLM using lightweight guardrails.

    Guardrails:
    - Must be a non-empty list of string tags.
    - Each tag is trimmed and checked for length between 2 and 40 characters.
    - If missing, invalid, or empty, defaults to fallback_tag (or "Technology").
    """
    if not isinstance(raw_tags, list):
        return [fallback_tag]

    clean_tags = []
    for tag in raw_tags:
        if isinstance(tag, str):
            stripped = tag.strip()
            if 2 <= len(stripped) <= 40:
                clean_tags.append(stripped)

    if not clean_tags:
        return [fallback_tag]
    return clean_tags[:3]


def generate_fallback_ai_digest_items(
    user_name: str, interest_tags: List[str]
) -> List[Dict[str, Any]]:
    """Generate 5 deterministic fallback items (3 interest-aligned + 2 open-ended exploratory).

    Guarantees zero duplicate (title, content) pairs across all 5 items, regardless of whether
    the user has 1, 2, 3, or 3+ interest tags specified. For >3 tags, samples evenly across the
    full list of interest tags to ensure representative topic coverage.

    Args:
        user_name: Display name of the target user.
        interest_tags: List of interest tags specified by the user.

    Returns:
        List[Dict[str, Any]]: List of 5 dicts ready for ActivityItem and DigestItem creation.
    """
    effective_tags = [t for t in interest_tags if t in INTEREST_TAXONOMY] if interest_tags else []
    if not effective_tags:
        effective_tags = INTEREST_TAXONOMY[:3]

    num_effective = len(effective_tags)
    ref_now = get_reference_now()
    synthetic_scores = [0.95, 0.92, 0.89, 0.86, 0.83]

    items: List[Dict[str, Any]] = []

    # Items 1-3 (Positions 1-3): Interest-Aligned Slots with tag_usage_count variant cycling.
    # For >3 tags, sample evenly across the full list instead of taking only the first 3.
    tag_usage_count: Dict[str, int] = {}
    for idx in range(3):
        if num_effective > 3:
            tag_idx = (idx * num_effective) // 3
            tag = effective_tags[tag_idx]
        else:
            tag = effective_tags[idx % num_effective]

        usage_idx = tag_usage_count.get(tag, 0)
        tag_usage_count[tag] = usage_idx + 1

        templates = FALLBACK_ITEM_TEMPLATES.get(tag, [])
        if templates:
            tmpl = templates[usage_idx % len(templates)]
            title = tmpl["title"]
            content = tmpl["content"]
            section = tmpl.get("section", f"{tag} Engineering")
        else:
            title = f"Emerging Innovations & Architecture Patterns in {tag} (Variant {usage_idx + 1})"
            content = f"An actionable technical breakdown of modern design patterns, toolchains, and community insights in {tag}."
            section = f"{tag} Engineering"

        items.append(
            {
                "title": title,
                "content": content,
                "category_tags": [tag],
                "section_title": section,
                "explanation_text": f"Tailored to your interest in {tag}",
                "relevance_score": synthetic_scores[idx],
                "rank_position": idx + 1,
                "created_at": ref_now,
                "engagement_metadata": {
                    "views": 140 - idx * 10,
                    "likes": 28 - idx * 2,
                    "shares": 7 - idx,
                    "is_ai_generated": True,
                },
            }
        )

    # Items 4-5 (Positions 4-5): Distinct Open-Ended Exploratory Slots
    user_tag_set = set(interest_tags or [])
    available_exploratory = [
        exp for exp in EXPLORATORY_FALLBACK_TOPICS if exp["tag"] not in user_tag_set
    ]
    if len(available_exploratory) < 2:
        available_exploratory = EXPLORATORY_FALLBACK_TOPICS

    for exp_idx, exp_topic in enumerate(available_exploratory[:2], start=3):
        items.append(
            {
                "title": exp_topic["title"],
                "content": exp_topic["content"],
                "category_tags": [exp_topic["tag"]],
                "section_title": exp_topic["section"],
                "explanation_text": exp_topic["explanation"],
                "relevance_score": synthetic_scores[exp_idx],
                "rank_position": exp_idx + 1,
                "created_at": ref_now,
                "engagement_metadata": {
                    "views": 110 - exp_idx * 10,
                    "likes": 20 - exp_idx * 2,
                    "shares": 5 - exp_idx,
                    "is_ai_generated": True,
                },
            }
        )

    return items


def build_ai_digest_prompt(user_name: str, interest_tags: List[str]) -> str:
    """Construct prompt for Claude to generate 5 open-ended activity updates (60/40 interest/explore ratio).

    Args:
        user_name: Name of target user.
        interest_tags: List of interest tags specified by user.

    Returns:
        str: Formatted prompt string for Claude API.
    """
    tags_str = ", ".join(interest_tags) if interest_tags else "general technology"
    num_tags = len(interest_tags) if interest_tags else 0

    if num_tags > 3:
        tailored_instruction = (
            f"Generate 3 updates covering a representative, diverse spread across {user_name}'s "
            f"{num_tags} followed interest topics ({tags_str}). Do NOT limit items 1-3 to only the first few tags in the list."
        )
    else:
        tailored_instruction = f"Generate updates directly tailored to {user_name}'s followed interest topics."

    return (
        f"You are an AI engineering curation assistant generating personalized technical activity updates for {user_name}.\n"
        f"{user_name} follows the following interest topics: {tags_str}.\n\n"
        "Instructions:\n"
        "1. Generate EXACTLY 5 distinct, high-quality, professional technical activity updates.\n"
        "2. TOPIC DISTRIBUTION:\n"
        f"   - ITEMS 1-3: {tailored_instruction}\n"
        "   - ITEMS 4-5: Generate open-ended, exploratory updates introducing emerging technology breakthroughs, adjacent tools, or novel engineering paradigms OUTSIDE {user_name}'s explicitly followed topics to promote discovery.\n"
        "3. OPEN-ENDED CATEGORIES: Category tags and section titles are open-ended and NOT constrained to any fixed taxonomy list. Use precise, descriptive open-ended tags (e.g. 'Autonomous Agents', 'Vector Search', 'Edge Computing', 'Quantum Error Correction', 'Compiler Design').\n"
        "4. For each item, provide:\n"
        "   - 'title': A compelling, professional technical title.\n"
        "   - 'content': A detailed 2-3 sentence technical description or breakdown.\n"
        "   - 'category_tags': A JSON array of 1-2 concise, descriptive category tag strings.\n"
        "   - 'section_title': A clean 2-4 word UI section category header for grouping related items (e.g. 'AI & Autonomous Systems', 'Quantum Computing', 'Cloud & Platform Engineering').\n"
        "   - 'explanation_text': A truthful, human-readable rationale phrase explaining why this update was selected (e.g. 'Tailored to your interest in Python', 'Exploratory update: Emerging trend in Vector Databases'). Do NOT claim deterministic database matching or fake numerical calculations.\n"
        "5. Return ONLY a valid JSON array of 5 objects. Do not include markdown codeblock wrappers, preambles, or conversational sign-offs.\n\n"
        'Example format:\n[\n  {\n    "title": "Architecting Autonomous AI Agents with Guardrails",\n    "content": "Explore modern patterns for multi-agent workflows combining state machines with LLM reasoning.",\n    "category_tags": ["AI Agents", "LLM Systems"],\n    "section_title": "AI & Autonomous Systems",\n    "explanation_text": "Tailored to your interest in AI"\n  }\n]'
    )


def call_llm_ai_digest_generator(
    user_name: str,
    interest_tags: List[str],
    client: Optional[Any] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> List[Dict[str, Any]]:
    """Execute API request to Anthropic Claude to generate 5 open-ended activity items.

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
        max_tokens=1200,
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
            fallback_primary_tag = interest_tags[0] if interest_tags else "Technology"

            results = []
            for idx, raw in enumerate(parsed[:5], start=1):
                raw_tags = raw.get("category_tags", [])
                valid_tags = sanitize_category_tags(raw_tags, fallback_primary_tag)
                section_title = str(
                    raw.get("section_title") or valid_tags[0] or "Featured Updates"
                ).strip()

                default_explanation = (
                    f"Tailored to your interest in {valid_tags[0]}"
                    if idx <= 3
                    else f"Exploratory topic: Emerging trend in {valid_tags[0]}"
                )

                results.append(
                    {
                        "title": str(raw.get("title", f"Technical Highlight #{idx}")),
                        "content": str(raw.get("content", "")),
                        "category_tags": valid_tags,
                        "section_title": section_title,
                        "explanation_text": str(
                            raw.get("explanation_text", default_explanation)
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
    """Generate 5 AI activity items for a user's digest (60/40 interest/explore ratio).

    Primary path calls Anthropic Claude API. Fallback path produces synthetic
    activity items if LLM is disabled or fails.

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
