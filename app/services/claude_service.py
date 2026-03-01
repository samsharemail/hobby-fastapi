import httpx
import os

async def generate_mermaid(architecture, detail_level):

    prompt = f"""
You are a senior software architect.

Generate a {detail_level} UML sequence diagram in Mermaid syntax.

Architecture Metadata:
Controllers: {architecture["controllers"]}
Services: {architecture["services"]}
Repositories: {architecture["repositories"]}
DbContexts: {architecture["dbcontexts"]}
Relationships: {architecture["relationships"]}

Requirements:
- Show Actor (User)
- Follow clean layered architecture
- Include error handling
- Output ONLY Mermaid code
"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": "CLAUDE_API_KEY",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    return response.json()["content"][0]["text"]