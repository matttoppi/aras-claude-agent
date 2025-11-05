# 🚀 Aras Innovator Claude Agent

> **Connect Claude Desktop to Aras Innovator PLM via OAuth 2.0!**

This Model Context Protocol (MCP) server enables Claude Desktop to interact with Aras Innovator or Innovator Edge through configurable authentication and REST APIs, allowing you to query PLM data, create items, and call methods directly from your AI assistant.

## ✨ What can you do?

- 🔐 **Secure authentication** with Aras Innovator OAuth 2.0 or Edge API keys
- 📊 **Query PLM data** using OData REST endpoints across supported backends  
- ✍️ **Create new items** (Parts, Documents, etc.) directly from Claude
- 🔧 **Call Aras server methods** or Edge REST operations
- 📋 **Access lists** and configuration data
- 🛡️ **Enterprise-grade security** with bearer token authentication

## 📋 Prerequisites

### 🐍 Python 3.8+
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **macOS/Linux:** `brew install python` or `sudo apt install python3 python3-pip`

### 🤖 Claude Desktop (free!)
- Download from [claude.ai](https://claude.ai/download) - no subscription required!

### 🏢 Aras Innovator 14+ or Innovator Edge
- Aras Innovator server with OAuth 2.0 endpoints enabled, or Innovator Edge environment access
- Valid credentials for the chosen backend (username/password/database for Aras, API key or token for Edge)
- Required API permissions

## 🎯 Quick start

### 1️⃣ Clone & install
```bash
git clone https://github.com/DaanTheoden/aras-claude-agent.git
cd aras-claude-agent
pip install -r requirements.txt
```

### 2️⃣ Configure your Aras connection
Create a `.env` file in the project root:
```env
# Core configuration
API_BACKEND=ARAS
API_URL=https://your-aras-server.com/YourDatabase
ARAS_DATABASE=YourDatabase
API_BASE_PATH=/Server/Odata
AUTH_MODE=ARAS_OAUTH
API_USERNAME=your-aras-username
API_PASSWORD=your-aras-password

# Optional configuration
API_TIMEOUT=30
API_RETRY_COUNT=3
API_RETRY_DELAY=1
LOG_LEVEL=INFO

# Innovator Edge overrides (uncomment if needed)
# API_BACKEND=EDGE
# API_BASE_PATH=
# EDGE_METHOD_PREFIX=methods
# AUTH_MODE=API_KEY
# EDGE_API_KEY_HEADER=Authorization
# EDGE_API_KEY=your-edge-api-key
# EDGE_BEARER_TOKEN=
# EDGE_BASIC_USER=
# EDGE_BASIC_PASS=
```

### 3️⃣ Add to Claude Desktop
Edit your Claude Desktop config file:

**📁 Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**📁 macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "api-server": {
      "command": "py",
      "args": ["C:/path/to/your/aras-claude-agent/main.py"]
    }
  }
}
```

> 💡 **Replace the path** with your actual installation directory!

### 4️⃣ Test your setup!

**Verify installation:**
```bash
python main.py
```
The server should start without any JSON parsing errors.

**Test in Claude Desktop:**
Restart Claude Desktop and try:
- *"Test my API connection"*
- *"Get all Parts from the database"*
- *"Show me the available Document types"*

## Multiple backends

Set `API_BACKEND` to choose between Aras Innovator and Innovator Edge. The default base path is `/Server/Odata` for Aras and blank for Edge, but you can override it with `API_BASE_PATH`. When using Edge, configure the authentication mode (`AUTH_MODE`) and the related credentials such as `EDGE_API_KEY`, `EDGE_BEARER_TOKEN`, or `EDGE_BASIC_USER` and `EDGE_BASIC_PASS`. The MCP tool set stays the same across both backends.

## 🛠️ Available tools

| Tool | Description | What You Can Ask | Example Endpoint |
|------|-------------|------------------|------------------|
| **`test_api_connection`** | Test OAuth 2.0 authentication | *"Test my API connection"* | N/A |
| **`api_get_items`** | Query configured OData endpoints | *"Get all Parts"* | `Part`, `Document` |
| **`api_create_item`** | Create items through the active backend | *"Create a new Part"* | `Part`, `Document` |
| **`api_call_method`** | Call server methods or Edge operations | *"Call method GetItemsInBOM"* | Method names |
| **`api_get_list`** | Get list values from the current backend | *"Show Part categories"* | List IDs |

## 🔐 Authentication

The default `AUTH_MODE=ARAS_OAUTH` uses the **Resource Owner Password Credentials Grant** with Aras Innovator 14+:

1. **Token Request**: `https://your-server/oauthserver/connect/token`
2. **Scope**: `openid Innovator offline_access`  
3. **Client ID**: `IOMApp` (default Aras client)
4. **Grant Type**: `password`
5. **Required**: `username`, `password`, `database`

Other supported modes:

- `API_KEY`: Adds an API key header defined by `EDGE_API_KEY_HEADER`.
- `EDGE_BEARER`: Uses a static bearer token from `EDGE_BEARER_TOKEN`.
- `BASIC`: Applies HTTP basic auth with `EDGE_BASIC_USER` and `EDGE_BASIC_PASS`.
- `NONE`: No authentication headers are sent.

## 💬 Example conversations

```
You: "Test my API connection"
Claude: ✅ Connection ready.
Backend: ARAS
Auth mode: ARAS_OAUTH
Base URL: https://your-server.com/YourDatabase

You: "Get all Parts where item_number starts with 'P-'"
Claude: Retrieved 25 Parts matching your criteria...

You: "Create a new Document with name 'User Manual v2'"
Claude: Successfully created Document with ID A1B2C3D4...
```

## 🔧 Recent Fixes & Updates

### ✅ v1.1.0 - OAuth 2.0 & JSON Parsing Fixes
- **Fixed**: "Unexpected token 'A', 'API MCP Se'... is not valid JSON" error
- **Added**: Proper OAuth 2.0 authentication with `requests-oauthlib`
- **Added**: Database parameter requirement for Aras authentication
- **Added**: Multiple backends via `API_BACKEND`, adjustable base paths, and method routing
- **Added**: Flexible auth modes (`ARAS_OAUTH`, `API_KEY`, `EDGE_BEARER`, `BASIC`, `NONE`)
- **Fixed**: All print statements redirected to stderr to prevent stdout contamination
- **Updated**: OData endpoint support (`/Server/Odata`) and default request headers

### 🛠️ Troubleshooting

**🔗 OAuth authentication failing?**
- Verify your Aras server supports OAuth 2.0 (Aras 14+)
- Check credentials and database name in `.env`
- Ensure user has API access permissions
- If you're using Innovator Edge, confirm `AUTH_MODE` matches the credentials supplied (`API_KEY`, `EDGE_BEARER`, or `BASIC`)

**🔐 "Missing database parameter" error?**
- Add `ARAS_DATABASE=YourDatabaseName` and keep `AUTH_MODE=ARAS_OAUTH`

**🤖 Claude not finding tools?**
- Restart Claude Desktop after config changes
- Check file paths in `claude_desktop_config.json`

**🐍 JSON parsing errors?**
- ✅ Fixed in v1.1.0! Update to latest version

## 🏗️ Architecture

```
Claude Desktop
    ↓ JSON-RPC
MCP Server (stdio)
    ↓ OAuth 2.0
Aras Innovator
    ↓ OData REST API
PLM Database
```

## 🤝 Contributing

Found a bug or want to add features? We welcome contributions! Please check our issues or submit a pull request.

## 📚 Learn More

- [Aras Developer Documentation](https://www.arasdeveloper.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Aras OAuth 2.0 Guide](https://community.aras.com)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details. 
