# Agno MCP Server

Agno MCP Server is a Model Context Protocol (MCP) server designed to provide AI assistants (such as Antigravity) with direct access to the [Agno](https://docs.agno.com/) framework documentation. Built using `FastMCP`, this server allows an AI agent to dynamically search, list, and read the contents of the Agno documentation to provide accurate and up-to-date answers.

## Features & Available Tools

The server exposes three main tools to the AI agent:

1. **`list_all_agno_sections()`**
   Retrieves a complete list of all available sections within the Agno documentation along with their respective URLs. 

2. **`get_agno_page_content(section_title: str)`**
   Fetches the actual text content of a specific documentation page. It uses caching to avoid redundant network requests.

3. **`search_relevant_agno_links(query: str)`**
   Searches the Agno documentation for a given query and returns the top 5 most relevant pages (titles and URLs) based on keyword matching.

## Prerequisites

- **Python 3.10+**
- Make sure to install the dependencies from the `requirements.txt` file within your virtual environment:
  ```bash
  pip install -r requirements.txt
  ```

## How to use with Antigravity

To integrate `agno_mcp_server` within the Antigravity AI assistant, you need to configure Antigravity's `mcp_config.json` file. By default, this file is located at `~/.gemini/antigravity/mcp_config.json`.

1. Open `mcp_config.json`.
2. Add the `agno_mcp_server` configuration under the `"mcpServers"` object. 
3. Ensure that you provide the **absolute paths** to the python executable inside your virtual environment and the `agno_mcp_server.py` script.

### Configuration Example

Below is the exact configuration block you need to add to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "agno_mcp_server": {
      "command": "/Users/alex/Desktop/programmazione/notebooks/My_notebooks/My_projects/my_mcp_servers/agno_mcp_server/agno_mcp_venv/bin/python",
      "args": [
        "/Users/alex/Desktop/programmazione/notebooks/My_notebooks/My_projects/my_mcp_servers/agno_mcp_server/agno_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/alex/Desktop/programmazione/notebooks/My_notebooks/My_projects/my_mcp_servers/agno_mcp_server"
      }
    }
  }
}
```

*Note: If you move the project folder, make sure to update the absolute paths in the `command`, `args`, and `env.PYTHONPATH` fields accordingly.*

## How it works under the hood

The server initializes an `AgnoDocumentationCatalog` to build a catalog of available documentation pages from the Agno sitemap. It utilizes an `AgnoDocumentationCache` to store previously fetched page contents, keeping response times quick. When the AI agent calls one of the exposed tools, `agno_mcp_server.py` routes the request to the corresponding logic in `tools.py` and returns the formatted textual data back to the agent.
