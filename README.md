# github-mcp-ext

GitHub MCP Server の機能拡張 — 標準の GitHub MCP サーバーにない操作を提供。

## 追加ツール

| ツール | 説明 |
|--------|------|
| `update_repo_visibility` | リポジトリを public/private に切替 |
| `update_repo` | リポジトリの description, topics, homepage 等を更新 |
| `delete_repo` | リポジトリ削除（確認必須） |

## セットアップ

```bash
git clone https://github.com/yasuhidekoizumi-afk/github-mcp-ext.git
cd github-mcp-ext
uv sync
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

## Hermes設定

```yaml
mcp_servers:
  github-mcp-ext:
    command: uv
    args: ["run", "github-mcp-ext"]
    cwd: /path/to/github-mcp-ext
    env:
      GITHUB_TOKEN: "ghp_xxx"
```

## License

MIT
