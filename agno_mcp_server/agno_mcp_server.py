# pip install "mcp[cli]"
# brew install node

# imports from tools_utils and definition of relevant objects
import tools_utils
from tools_utils import BASE_URL, SITEMAP_URL, BASE_CATALOG

catalog = tools_utils.AgnoDocumentationCatalog(SITEMAP_URL, BASE_CATALOG)
populated_catalog = catalog.build_catalog()
cache = tools_utils.AgnoDocumentationCache()

# imports from tools
import tools
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("agno_mcp_server")

@mcp.tool()
def list_all_agno_sections() -> dict:
    """Return all the sections of the Agno documentation with their urls."""

    return tools.list_all_agno_sections(populated_catalog)

@mcp.tool()
def get_agno_page_content(section_title: str = "introduction") -> str:
    """Return the content of a specific page of the Agno documentation given a section name.
    
    Args:
        section_title (str): The name of the section to retrieve the content of.
    
    Returns:
        str: The content of the specified section.
    """

    return tools.get_agno_page_content(section_title, populated_catalog, cache)

TOP_K_RESULTS = 5 # the number of results to return from the documentation search
@mcp.tool()
def search_relevant_agno_links(query: str) -> str:
    """Search the Agno documentation for a specific query and return the results.
    
    Args:
        query (str): The query to search for.
    
    Returns:
        str: The results of the search.
    """

    return tools.search_relevant_agno_links(query, populated_catalog, cache, TOP_K_RESULTS)    


def main() -> None:
    mcp.run(transport = "stdio")

if __name__ == "__main__":
    main()