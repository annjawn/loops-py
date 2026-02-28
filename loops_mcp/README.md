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
uv sync --extra dev --extra mcp
```

## Configuration

Required:

- `LOOPS_API_KEY`

Optional (Loops client):

- `LOOPS_BASE_URL` (default: `https://app.loops.so/api/v1`)
- `LOOPS_TIMEOUT` (default: `30`)
- `LOOPS_MAX_RETRIES` (default: `3`)
- `LOOPS_RETRY_BACKOFF_BASE` (default: `0.25`)
- `LOOPS_RETRY_BACKOFF_MAX` (default: `4.0`)
- `LOOPS_RETRY_JITTER` (default: `0.1`)
- `LOOPS_USER_AGENT` (default: `loops-mcp/1.0`)

Optional (server transport):

- `MCP_TRANSPORT` — `stdio` (default), `sse`, or `streamable-http`
- `MCP_HOST` (default: `0.0.0.0`)
- `MCP_PORT` (default: `8000`)

## Run server

Local (stdio, default):

```bash
LOOPS_API_KEY="your_key" uv run python loops_mcp/server.py
```

Remote (SSE over HTTP):

```bash
LOOPS_API_KEY="your_key" MCP_TRANSPORT=sse MCP_PORT=8000 uv run python loops_mcp/server.py
```

Remote (Streamable HTTP):

```bash
LOOPS_API_KEY="your_key" MCP_TRANSPORT=streamable-http MCP_PORT=8000 uv run python loops_mcp/server.py
```

## MCP client config

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "loops": {
      "command": "uv",
      "args": ["run", "python", "loops_mcp/server.py"],
      "cwd": "/absolute/path/to/loops-py",
      "env": {
        "LOOPS_API_KEY": "your_key"
      }
    }
  }
}
```

### Claude Code

Add a `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "loops": {
      "command": "uv",
      "args": ["run", "python", "loops_mcp/server.py"],
      "env": {
        "LOOPS_API_KEY": "your_key"
      }
    }
  }
}
```

### Using a .env file (recommended)

To avoid storing the API key in plaintext config files, create a gitignored `.env`:

```
export LOOPS_API_KEY="loops_sk_..."
```

Then reference it in your client config:

```json
{
  "mcpServers": {
    "loops": {
      "command": "bash",
      "args": ["-c", "source .env && uv run python loops_mcp/server.py"],
      "cwd": "/absolute/path/to/loops-py"
    }
  }
}
```

## Remote deployment

To expose the MCP server as an HTTP endpoint, use the `sse` or `streamable-http` transport.

### Docker

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --extra mcp
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
EXPOSE 8000
CMD ["uv", "run", "python", "loops_mcp/server.py"]
```

```bash
docker build -t loops-mcp .
docker run -p 8000:8000 -e LOOPS_API_KEY="your_key" loops-mcp
```

### Connecting a remote MCP client

Once the server is running remotely (e.g. at `https://mcp.example.com`), configure
your client to connect via SSE or Streamable HTTP instead of stdio:

```json
{
  "mcpServers": {
    "loops": {
      "url": "https://mcp.example.com/sse"
    }
  }
}
```

For Streamable HTTP:

```json
{
  "mcpServers": {
    "loops": {
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

### Production considerations

- Put a reverse proxy (nginx, Caddy) in front for TLS termination.
- Set `LOOPS_API_KEY` via your platform's secrets manager (e.g. Docker secrets,
  AWS Secrets Manager, Fly.io secrets) — never bake it into the image.
- The MCP SDK does not provide built-in auth for the HTTP endpoint.
  Use your reverse proxy or a sidecar to add API key / OAuth verification
  before traffic reaches the MCP server.
