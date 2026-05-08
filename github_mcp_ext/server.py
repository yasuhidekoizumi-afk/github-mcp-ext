"""GitHub REST API tools missing from official MCP server."""
import os
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import httpx

server = Server("github-mcp-ext")
API = "https://api.github.com"


def _client():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN env var (ghp_xxx or fine-grained PAT)")
    return httpx.Client(
        base_url=API,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="update_repo_visibility",
            description="Make a repository public or private. Owner must match the token user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "make_public": {"type": "boolean", "description": "true=public, false=private"},
                },
                "required": ["owner", "repo", "make_public"],
            },
        ),
        Tool(
            name="update_repo",
            description="Update repository settings: description, homepage, topics, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "description": {"type": "string"},
                    "homepage": {"type": "string"},
                    "has_issues": {"type": "boolean"},
                    "has_projects": {"type": "boolean"},
                    "has_wiki": {"type": "boolean"},
                },
                "required": ["owner", "repo"],
            },
        ),
        Tool(
            name="delete_repo",
            description="Delete a repository. Requires explicit confirmation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "confirm": {"type": "boolean", "description": "Must be true to confirm deletion"},
                },
                "required": ["owner", "repo", "confirm"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    c = _client()
    try:
        if name == "update_repo_visibility":
            return await _visibility(arguments, c)
        elif name == "update_repo":
            return await _update(arguments, c)
        elif name == "delete_repo":
            return await _delete(arguments, c)
        return [TextContent(type="text", text=f"Unknown: {name}")]
    finally:
        c.close()


async def _visibility(args: dict, c: httpx.Client) -> list[TextContent]:
    owner, repo = args["owner"], args["repo"]
    private = not args["make_public"]
    r = c.patch(f"/repos/{owner}/{repo}", json={"private": private})
    r.raise_for_status()
    vis = "public" if args["make_public"] else "private"
    return [TextContent(type="text", text=f"✅ {owner}/{repo} is now **{vis}**")]


async def _update(args: dict, c: httpx.Client) -> list[TextContent]:
    owner, repo = args["owner"], args["repo"]
    payload = {}
    for k in ("description", "homepage"):
        if k in args:
            payload[k] = args[k]
    for k in ("has_issues", "has_projects", "has_wiki"):
        if k in args:
            payload[k] = args[k]
    r = c.patch(f"/repos/{owner}/{repo}", json=payload)
    r.raise_for_status()
    return [TextContent(type="text", text=f"✅ {owner}/{repo} updated: {json.dumps(payload)}")]


async def _delete(args: dict, c: httpx.Client) -> list[TextContent]:
    if not args.get("confirm"):
        return [TextContent(type="text", text="❌ Set confirm=true to proceed")]
    owner, repo = args["owner"], args["repo"]
    r = c.delete(f"/repos/{owner}/{repo}")
    if r.status_code == 204:
        return [TextContent(type="text", text=f"✅ {owner}/{repo} deleted")]
    r.raise_for_status()


def main():
    import asyncio
    asyncio.run(_run())


async def _run():
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    main()
