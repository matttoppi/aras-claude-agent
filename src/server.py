#!/usr/bin/env python3
"""
Generic API MCP Server
Created by D. Theoden
Date: June 12, 2025
"""

import asyncio
import json
import sys
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from .api_client import APIClient
from .config import BACKEND, AUTH_MODE

server = Server("api-mcp-server")
api_client = APIClient()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for API integration."""
    return [
        types.Tool(
            name="test_api_connection",
            description="Test connection and authentication with API server",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="api_get_items",
            description="GET operation - Retrieve items from API",
            inputSchema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The API endpoint to retrieve data from",
                    },
                    "expand": {
                        "type": "string",
                        "description": "Optional: expand parameter for related data",
                    },
                    "filter": {
                        "type": "string", 
                        "description": "Optional: filter parameter for filtering results",
                    },
                    "select": {
                        "type": "string",
                        "description": "Optional: select parameter for specific fields",
                    },
                    "auto_resolve": {
                        "type": "boolean",
                        "description": "Optional: automatically resolve friendly item type aliases",
                    },
                },
                "required": ["endpoint"],
            },
        ),
        types.Tool(
            name="api_create_item",
            description="POST operation - Create new items using API",
            inputSchema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The API endpoint to create data at",
                    },
                    "data": {
                        "type": "object",
                        "description": "The item data as JSON object",
                    }
                },
                "required": ["endpoint", "data"],
            },
        ),
        types.Tool(
            name="api_call_method",
            description="Call API server methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "method_name": {
                        "type": "string",
                        "description": "The method name to call",
                    },
                    "data": {
                        "type": "object",
                        "description": "The method parameters as JSON object",
                    }
                },
                "required": ["method_name", "data"],
            },
        ),
        types.Tool(
            name="api_get_list",
            description="Get list items from API",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "The list ID to retrieve values from",
                    },
                    "expand": {
                        "type": "string",
                        "description": "Optional: expand parameter for list values",
                    }
                },
                "required": ["list_id"],
            },
        ),
        types.Tool(
            name="api_get_metadata",
            description="Return raw OData $metadata (CSDL) from the API for inspection",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="api_list_itemtypes",
            description="List available item types (entity sets) discovered from $metadata",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="api_resolve_itemtype",
            description="Resolve a user-supplied label/alias to a valid entity set (uses $metadata + fuzzy matching)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Candidate item type label, e.g., 'PR' or 'Problem Report'",
                    },
                },
                "required": ["name"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for API operations."""
    
    try:
        if name == "test_api_connection":
            # Test authentication and get bearer token
            authenticated = api_client.authenticate()
            if authenticated:
                base_url = api_client.url or ''
                if api_client.base_path:
                    base_url = f"{base_url.rstrip('/')}/{api_client.base_path.lstrip('/')}"
                return [types.TextContent(
                    type="text",
                    text=(
                        "Connection ready.\n"
                        f"Backend: {BACKEND}\n"
                        f"Auth mode: {AUTH_MODE}\n"
                        f"Base URL: {base_url}"
                    )
                )]
            else:
                return [types.TextContent(
                    type="text", 
                    text="Failed to authenticate with API. Please check your credentials."
                )]
        
        elif name == "api_get_items":
            if not arguments or "endpoint" not in arguments:
                raise ValueError("Endpoint is required")
            
            item_data = api_client.get_items(
                arguments["endpoint"],
                expand=arguments.get("expand"),
                filter_param=arguments.get("filter"),
                select=arguments.get("select"),
                auto_resolve=arguments.get("auto_resolve"),
            )
            resolution_note = ""
            if isinstance(item_data, dict):
                resolution_note = item_data.get('_meta', {}).get('endpoint_resolution', '')
            suffix = f" [{resolution_note}]" if resolution_note else ""
            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Retrieved items from {arguments['endpoint']}{suffix}:\n"
                        f"{json.dumps(item_data, indent=2)}"
                    )
                )
            ]
        
        elif name == "api_create_item":
            if not arguments or "endpoint" not in arguments or "data" not in arguments:
                raise ValueError("Endpoint and data are required")
            
            result = api_client.create_item(arguments["endpoint"], arguments["data"])
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully created item at {arguments['endpoint']}:\n{json.dumps(result, indent=2)}"
                )
            ]
        
        elif name == "api_call_method":
            if not arguments or "method_name" not in arguments or "data" not in arguments:
                raise ValueError("Method name and data are required")
            
            result = api_client.call_method(arguments["method_name"], arguments["data"])
            return [
                types.TextContent(
                    type="text",
                    text=f"Method {arguments['method_name']} result:\n{json.dumps(result, indent=2)}"
                )
            ]
        
        elif name == "api_get_list":
            if not arguments or "list_id" not in arguments:
                raise ValueError("List ID is required")
            
            list_data = api_client.get_list(
                arguments["list_id"],
                expand=arguments.get("expand")
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"List {arguments['list_id']} data:\n{json.dumps(list_data, indent=2)}"
                )
            ]
        
        elif name == "api_get_metadata":
            metadata = api_client.get_metadata_raw()
            return [
                types.TextContent(
                    type="text",
                    text=metadata
                )
            ]

        elif name == "api_list_itemtypes":
            index = api_client._get_schema_index()
            entities = index.get('entities', {})
            pretty = [
                {
                    "entity_set": key,
                    **value,
                }
                for key, value in sorted(entities.items())
            ]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(pretty, indent=2)
                )
            ]

        elif name == "api_resolve_itemtype":
            if not arguments or "name" not in arguments:
                raise ValueError("Name is required")
            resolution = api_client.resolve_endpoint(arguments["name"])
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(resolution, indent=2)
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as error:
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(error)}"
            )
        ]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Note: Don't print to stdout as it interferes with JSON-RPC protocol
        # Emit a startup notice to stderr so users know we're waiting on stdio.
        # print("[api-mcp-server] Started; waiting for JSON-RPC on stdio (Claude Desktop)", file=sys.stderr, flush=True)
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="api-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 
