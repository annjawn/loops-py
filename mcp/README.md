# Loops MCP Server

This directory contains a ready-to-run MCP server that exposes all supported
Loops API operations as MCP tools using `pyloops-so`.

## Included tools

- `create_contact`
- `update_contact`
- `find_contact`
- `delete_contact`
- `create_contact_property`
- `list_contact_properties`
- `list_mailing_lists`
- `send_event`
- `send_transactional_email`
- `list_transactional_emails`
- `verify_api_key`
- `list_dedicated_sending_ips`

## Prerequisites

- Python 3.9+
- `uv`

Install dependencies (from repo root):

```bash
uv sync --extra dev
uv add mcp
```

## Configuration

Required:

- `LOOPS_API_KEY`

Optional:

- `LOOPS_BASE_URL` (default: `https://app.loops.so/api/v1`)
- `LOOPS_TIMEOUT` (default: `30`)
- `LOOPS_MAX_RETRIES` (default: `3`)
- `LOOPS_RETRY_BACKOFF_BASE` (default: `0.25`)
- `LOOPS_RETRY_BACKOFF_MAX` (default: `4.0`)
- `LOOPS_RETRY_JITTER` (default: `0.1`)
- `LOOPS_USER_AGENT` (default: `loops-mcp/1.0`)

## Run server

```bash
LOOPS_API_KEY="your_key" uv run python mcp/server.py
```

## Example MCP client config (stdio)

```json
{
  "mcpServers": {
    "loops": {
      "command": "uv",
      "args": ["run", "python", "mcp/server.py"],
      "env": {
        "LOOPS_API_KEY": "your_key"
      }
    }
  }
}
```
