# here we define the tools that will be used by the Agno MCP server.

from pygments.token import Error
from tools_utils import scrape_page_from_url, get_slug_from_url, AgnoDocumentationCatalog, AgnoDocumentationCache
from tools_utils import BASE_URL, SITEMAP_URL, BASE_CATALOG



def check_status(populated_catalog: list[dict[str, str]] = None,
                 cache: AgnoDocumentationCache = None) -> list:
    if populated_catalog is None:
        catalog = AgnoDocumentationCatalog(SITEMAP_URL, BASE_CATALOG)
        populated_catalog = catalog.build_catalog()
    if cache is None:
        cache = AgnoDocumentationCache()

    return populated_catalog, cache

########################################################################################
###################################### FIRST TOOL ######################################
########################################################################################
def list_all_agno_sections(populated_catalog: list[dict[str, str]] = None) -> str: # must give string to be readable by the agent
    """Return all the sections of the Agno documentation with their urls.
    
    Args:
        populated_catalog (list[dict[str, str]]): The catalog of the Agno documentation.
    
    Returns:
        str: The content of the specified section.
    """
    if populated_catalog is None:
        catalog = AgnoDocumentationCatalog(SITEMAP_URL, BASE_CATALOG)
        populated_catalog = catalog.build_catalog()
    textual_catalog = ""
    for item in populated_catalog:
        textual_catalog += f"Section name: {item['title']} | Url: {item['url']} \n\n"
    return textual_catalog

#########################################################################################
###################################### SECOND TOOL ######################################
#########################################################################################

# the following is an auxiliary function for 'get_agno_page_content' function
def check_if_url_exists(url: str, populated_catalog: list[dict[str, str]]) -> bool:
    """Check if a url exists in the Agno documentation.
    
    Args:
        url (str): The url to check.
        populated_catalog (list[dict[str, str]]): The catalog of the Agno documentation.
    
    Returns:
        bool: True if the url exists in the Agno documentation, False otherwise.
    """
    return url in [item["url"] for item in populated_catalog]
    
# the following is an auxiliary function for 'get_agno_page_content' function
def get_section_url(section_title: str, populated_catalog: list[dict[str, str]]) -> str:
    """Get the url of a specific section of the Agno documentation given a section name.
    
    Args:
        section_title (str): The name of the section to retrieve the url of.
        populated_catalog (list[dict[str, str]]): The catalog of the Agno documentation.
    
    Returns:
        str: The url of the specified section.
    """
    try:
        return [item["url"] for item in populated_catalog if item["title"] == section_title][0]
    except Exception as e:
        return f"ERROR: page '{section_title}' not found in the Agno documentation. Try to use the 'list_all_agno_sections' tool to see the available sections."
    
# This second tool answers to "how to search in the Agno documentation?"
def get_agno_page_content(section_title: str, 
                          populated_catalog: list[dict[str, str]] = None,
                          cache: AgnoDocumentationCache = None) -> str:
    """Return the content of a specific page of the Agno documentation given a section name.
    
    Args:
        section_title (str): The name of the section to retrieve the content of.
        populated_catalog (list[dict[str, str]]): The catalog of the Agno documentation.
    
    Returns:
        str: The content of the specified section.
    """

    section_title = section_title.lower().strip()
    populated_catalog, cache = check_status(populated_catalog, cache) # check if cache and catalog are initialized/populated
    
    if check_if_url_exists(section_title, populated_catalog): # if the LLM passes the url instead of the title
        section_url = section_title
    else:
        section_url = get_section_url(section_title, populated_catalog) # if the section does not exist, section_url starts with 'ERROR:...'

    if section_url.startswith("ERROR"):
        return section_url
    else:
        if cache.get_content(section_url):
            content = cache.get_content(section_url)
        else:
            content = scrape_page_from_url(section_url) # if it fails, it returns an ERROR message that must be filtered
            if not content.startswith("ERROR"):
                cache.add_content(section_url, content)
        return content
    
#########################################################################################
###################################### THIRD TOOL #######################################
#########################################################################################
# This third tool answers to "what are the most relevant pages in the Agno documentation for a specific query?"

# the following is an auxiliary function for 'search_agno_docs' function
def compute_number_matches(query_words: list[str], 
                           section_title_words: list[str]) -> int:
    """Compute the number of matches between query words and section title words.
    
    Args:
        query_words (list[str]): The words of the query.
        section_title_words (list[str]): The words of the section title.
    
    Returns:
        int: The number of matches between query words and section title words.
    """
    number_matches = 0
    for query_word in query_words:
        variants = {query_word, query_word[:-1], query_word+"s", query_word+"ed", query_word+"ing"}
        if any(variant in section_title_words for variant in variants if variant): 
            number_matches += 1
    return number_matches

# the following is an auxiliary function for 'search_agno_docs' function
def improve_ordering(sorted_catalog: list[dict[str, str]], top_k: int) -> list[dict[str, str]]:
    minimun_number_matches = sorted_catalog[top_k-1]["number_matches"]
    reduced_catalog = [item for item in sorted_catalog if item["number_matches"] >= minimun_number_matches]
    # Now reduced_catalog is the catalog with all the important matches, but it can be larger than top_k
    # Among the items with the same number of matches, we want to return the ones that are more relevant to the query
    # The shorter is the link, the more relevant it is
    for item in reduced_catalog:
        item["url_length"] = len(item["url"])
    
    # now sort the reduced catalog by the url length
    sorted_reduced_catalog = sorted(
        reduced_catalog, 
        key = lambda x: (-x["number_matches"], len(x["url"]))
    )

    top_k_results = sorted_reduced_catalog[:top_k]
    top_interesting_results = top_k_results.copy()

    # remove all the items with 0 matches, so we can have less than top_k results
    for item in top_k_results:
        if item["number_matches"] == 0:
            top_interesting_results.remove(item)
    
    # return the top interesting results
    return top_interesting_results

import re
def search_relevant_agno_links(query: str, 
                               populated_catalog: list[dict[str, str]] = None,
                               cache: AgnoDocumentationCache = None,
                               top_k: int = 5) -> str:
    """Search the Agno documentation for a specific query and return the top_k matching results.
    This function does not return the content of the pages, but the titles and urls of the pages.
    
    Args:
        query (str): The query to search for.
        populated_catalog (list[dict[str, str]]): The catalog of the Agno documentation.
        cache (AgnoDocumentationCache): The cache of the Agno documentation.
        top_k (int): The number of results to return.
    
    Returns:
        str: The results of the search.
    """

    populated_catalog, cache = check_status(populated_catalog, cache) # check if cache and catalog are initialized/populated
    
    query_words = query.lower().strip().split()

    # now count the number of query words in each section title
    for item in populated_catalog:
        section_title = item["title"].lower().strip()
        section_title_words = re.split(r'[/,-]+', section_title)
        number_matches = compute_number_matches(query_words, section_title_words)
        item["number_matches"] = number_matches

    # now sort the catalog by the number of matches
    sorted_catalog = sorted(populated_catalog, key = lambda x: x["number_matches"], reverse = True)
    top_interesting_results = improve_ordering(sorted_catalog, top_k)
    
    
    if not top_interesting_results: # if no results are found
        return f"No results found for the query: {query}. Use 'list_all_agno_sections()' to see all the available sections."

    # now return the the remaining top results in string format
    textual_catalog = ""
    for item in top_interesting_results:
        textual_catalog += f"Section name: {item['title']} | Url: {item['url']} (call get_agno_page_content('{item['title']}') to read the content)\n\n"
    return textual_catalog
 

# simple tests

# print(get_agno_page_content("teams"))
# print(search_relevant_agno_links("build teams"))
    

    

    
    

    
    