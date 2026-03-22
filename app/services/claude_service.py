import os
import re
from typing import Any, Dict, Optional

import httpx

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
# Strong at structured outputs and code; widely available on Anthropic API.
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


def _get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")


def extract_mermaid_block(text: str) -> str:
    """Pull Mermaid source from model output (strip markdown fences)."""
    text = text.strip()
    fence = re.search(r"```(?:mermaid)?\s*\n([\s\S]*?)```", text)
    if fence:
        return fence.group(1).strip()
    if "sequenceDiagram" in text:
        start = text.find("sequenceDiagram")
        tail = text[start:]
        if "```" in tail:
            tail = tail.split("```", 1)[0]
        return tail.strip()
    return text


def _build_prompt(
    architecture: Dict[str, Any],
    detail_level: str,
    selected_controller: Optional[str],
) -> str:
    focus = ""
    if selected_controller:
        focus = (
            f"\nFocus the main HTTP flow on controller: {selected_controller}. "
            "Show User → that controller → its collaborators (services, repositories, DbContext) "
            "based on the relationships below. Omit unrelated endpoints.\n"
        )
    else:
        focus = (
            "\nProvide a compact overview: cover the most important controllers and their "
            "typical call chain (limit participants to avoid clutter).\n"
        )

    return f"""You are a senior .NET architect.

Generate a {detail_level} UML sequence diagram as **Mermaid** `sequenceDiagram` syntax only.

Architecture (from static analysis of the uploaded project):
- Controllers: {architecture.get("controllers", [])}
- Services: {architecture.get("services", [])}
- Repositories: {architecture.get("repositories", [])}
- DbContexts: {architecture.get("dbcontexts", [])}
- Minimal APIs (endpoint maps): {architecture.get("minimal_apis", [])}
- Inferred relationships (class/file → dependency): {architecture.get("relationships", [])}
{focus}
Rules:
- Start with `sequenceDiagram` on its own line.
- Include `actor User` (or `participant User` if needed).
- Use short, valid participant aliases (no spaces in IDs; use `participant X as "Label"` for display names).
- Reflect layered flow: HTTP → controller/minimal API → application services → repositories → DbContext where relationships suggest it.
- Optionally show alt/opt for validation or errors if it fits {detail_level} detail.
- Output **only** the Mermaid diagram text — no prose, no markdown outside one ```mermaid fenced block is optional; plain diagram lines are fine.
"""


async def generate_mermaid_with_claude(
    architecture: Dict[str, Any],
    detail_level: str = "medium",
    selected_controller: Optional[str] = None,
) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    prompt = _build_prompt(architecture, detail_level, selected_controller)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()

    blocks = data.get("content") or []
    text_parts = []
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))
    raw = "\n".join(text_parts).strip()
    if not raw:
        raise ValueError("Empty response from Claude")

    mermaid = extract_mermaid_block(raw)
    if "sequenceDiagram" not in mermaid:
        raise ValueError("Model did not return a sequenceDiagram")
    return mermaid
