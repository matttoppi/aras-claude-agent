# 🚀 Aras Innovator Claude Agent

> **Connect Claude Desktop to Aras Innovator PLM through the Model Context Protocol (MCP)**

This MCP server lets Claude Desktop securely interact with Aras Innovator using either **Aras InnovatorEdge** or **Configurable Web Services (CWS)**. It exposes a set of structured tools that allow Claude to query PLM data, explore metadata, create items, call methods, and more—all through natural language.

## ✨ What can you do?

* 🔐 **Authenticate securely** using API key–based access
* 📊 **Query PLM data** over REST/OData
* 🧠 **Explore your schema** via `$metadata` discovery
* ✍️ **Create Items** (Part, Document, custom ItemTypes, etc.)
* 🔧 **Call Aras server methods**
* 🔄 **Automatically resolve ItemTypes** using fuzzy matching
* 🛡️ **Edge-first design** with full compatibility for CWS

---

## 📋 Prerequisites

### 🐍 Python 3.8+

* Windows/macOS/Linux supported

### 🤖 Claude Desktop

* Download from [https://claude.ai/download](https://claude.ai/download)
* No subscription required

### 🏢 Aras Innovator (CWS or Edge)

This agent supports:

* **Aras InnovatorEdge** (API-key access)
* **Aras Innovator REST via CWS** (standard /Server/OData endpoint)

Both backends use the **same config pattern**.

---

## 🎯 Quick start

### 1️⃣ Clone & install

```bash
git clone https://github.com/ArasLabs/aras-claude-agent.git
cd aras-claude-agent
pip install -r requirements.txt
```

---

## 2️⃣ Configure your connection

Create a `.env` file in the project root.

### **Option A — InnovatorEdge backend**

```env
API_BACKEND=EDGE
AUTH_MODE=API_KEY
EDGE_API_KEY=your_edge_api_key
API_URL=https://yourserver.com/InnovatorServer

# Optional
ITEMTYPE_ALIASES=Problem:PR;Doc:Document;Part:Part
```

### **Option B — Configurable Web Services (CWS) backend**

> Uses the same API-key auth pattern for compatibility.

```env
API_BACKEND=ARAS
AUTH_MODE=API_KEY
EDGE_API_KEY=your_cws_api_key      # Works for CWS even though named EDGE_API_KEY
API_URL=https://yourserver.com/InnovatorServer

ITEMTYPE_ALIASES=Problem:PR;Doc:Document;Part:Part
```

Notes:

* You **do not** need to manually append `/Server/Odata`; this is handled internally.
* The server normalizes URLs and applies the correct request pattern for Edge or CWS automatically.

---

## 3️⃣ Add to Claude Desktop

Edit:

* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aras-api": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/aras-claude-agent"
    }
  }
}
```

Restart Claude Desktop.

---

## 4️⃣ Verify the server

```bash
python -m src.server
```

If it starts and waits silently, your environment is correct. Claude will launch it automatically when needed.

---

## 🛠️ Available tools

| Tool                   | Description                         | Example prompt                         |
| ---------------------- | ----------------------------------- | -------------------------------------- |
| `test_api_connection`  | Confirm connectivity + auth         | “Test my API connection.”              |
| `api_get_items`        | Query any ItemType via OData        | “Get all Parts.”                       |
| `api_create_item`      | Create a new Aras item              | “Create a new Document named TestDoc.” |
| `api_call_method`      | Invoke Aras server methods          | “Call GetItemsInBOM.”                  |
| `api_get_list`         | Fetch list values                   | “Show Part classifications.”           |
| `api_get_metadata`     | Download and inspect `$metadata`    | “Show me all ItemTypes.”               |
| `api_resolve_itemtype` | Map friendly names → real ItemTypes | “What ItemType is ‘Doc’?”              |
| `api_list_itemtypes`   | List ItemTypes discovered from CSDL | “List available ItemTypes.”            |

---

## 🔧 Authentication details

This project uses a simple API-key model compatible with:

### **Aras InnovatorEdge**

* Direct API key header

### **CWS (standard Aras REST)**

* Same API key header style
* Server automatically adapts request format to CWS/Innovator REST

No OAuth 2.0 configuration is required for the CWS or Edge flows described above.

---

## 💬 Example conversations

```
You: "Test my API connection."
Claude: ✓ Successfully authenticated. Ready for API calls.

You: "Create 10 Parts numbered ROBOT-001 to ROBOT-010."
Claude: Created 10 Part items.

You: "Get all Problem Reports assigned to me."
Claude: Retrieved 12 PR items.
```

---

## 🏗️ Architecture

```
Claude Desktop
      ↓ JSON-RPC MCP
Python MCP Server
      ↓ Edge or CWS REST API
Aras Innovator
      ↓ OData / metadata / methods
PLM Database
```

---

## 🔍 CWS & Edge Support (Summary)

| Feature                         | InnovatorEdge | CWS |
| ------------------------------- | ------------- | --- |
| API key auth                    | ✔             | ✔   |
| OData metadata discovery        | ✔             | ✔   |
| Item creation                   | ✔             | ✔   |
| Method calls                    | ✔             | ✔   |
| Automatic URL normalization     | ✔             | ✔   |
| Name → ItemType resolution      | ✔             | ✔   |
| Schema-aware test data creation | ✔             | ✔   |

Both backends provide the **same toolset** to Claude—no prompt changes required.

---

## 🛠️ Troubleshooting

* **Authentication errors** → check `API_BACKEND`, `API_URL`, and `EDGE_API_KEY`
* **Claude not seeing tools** → restart Claude Desktop
* **Metadata not loading** → confirm `/Server/OData` is reachable (CWS) or API-key access is enabled (Edge)

---

## 🤝 Contributing

Issues and pull requests are welcome!

---

## 📄 License

MIT License — see [LICENSE](LICENSE).