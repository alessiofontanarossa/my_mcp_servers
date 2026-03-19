##############################################################################################
###################################### SCRAPER FUNCTION ######################################
##############################################################################################

# a tool to scrape a page given an url, returning the content in markdown format to avoid tokens usage
 
# pip install html2text httpx
import html2text # to convert html to markdown
import httpx # to make http requests, faster than 'requests' library

def scrape_page_from_url(url: str) -> str:

    """Scrape the content of a URL, returning it as plain text. 
    
    Args:
        url (str): The URL to scrape.
    
    Returns:
        str: The content of the URL as plain text."""

    converter = html2text.HTML2Text()

    # config the converter
    converter.ignore_links = True
    converter.ignore_images = True
    converter.body_width = 0 # no wrap

    try:
        with httpx.Client(timeout = 10, # if the Agno website is temporarily down
                          follow_redirects = True) as client:
            response = client.get(url)
            response.raise_for_status() # raise error if the status code is not 200
            html_text = response.text # heavy html text, with tags, links ecc
            return converter.handle(html_text) # clean text in mardown format to avoid tokens usage
    except httpx.HTTPStatusError as exc:
        return f"ERROR: impossible to scrape {url}: HTTP error {exc.response.status_code}"
    except Exception as exc:
        return f"ERROR: impossible to scrape {url}: {exc}"

###################################################################################################
###################################### DOCUMENTATION CATALOG ######################################
###################################################################################################

# A class to navigate the entire Agno framework documentation.
# the structure of the sitemap page is:
# <urlset>
#
#     <url>
#         <loc>https://docs.agno.com/workflows/workflow-patterns/step-based-workflow</loc>
#         <lastmod>2026-01-29T00:37:17.463Z</lastmod>
#     </url>
#
#     <url>
#       <loc>https://docs.agno.com/workflows/workflow-tools</loc>
#       <lastmod>2026-01-29T00:37:17.477Z</lastmod>
#     </url>
#
# </urlset>

# Before implementing the class, we need a function to extract the slug from the url.
# Example: https://docs.agno.com/workflows/workflow-patterns -> workflows/workflow-patterns

def get_slug_from_url(url: str) -> str:
    """Extract the slug from a URL."""
    try:
        return url.replace("https://docs.agno.com/", "")
    except Exception as e: # if the url is not from docs.agno.com, return the url as is
        return url
        
# pip install beautifulsoup4 lxml
import os 
from bs4 import BeautifulSoup

BASE_URL = "https://docs.agno.com/"
SITEMAP_URL = os.path.join(BASE_URL, "sitemap.xml")

BASE_CATALOG: list[dict[str, str]] = [
    {"title": "agents", "url": os.path.join(BASE_URL, "agents"),  "description": ""},
    {"title": "teams", "url": os.path.join(BASE_URL, "teams"), "description": ""},
    {"title": "memory", "url": os.path.join(BASE_URL, "memory"), "description": ""},
    {"title": "database", "url": os.path.join(BASE_URL, "database"), "description": ""},
    {"title": "knowledge", "url": os.path.join(BASE_URL, "knowledge"), "description": ""},
    {"title": "models", "url": os.path.join(BASE_URL, "models"), "description": ""},
    {"title": "tools", "url": os.path.join(BASE_URL, "tools"), "description": ""},
    {"title": "workflows", "url": os.path.join(BASE_URL, "workflows"), "description": ""},
]

class AgnoDocumentationCatalog:
    def __init__(self, sitemap_url: str, base_catalog: list[dict[str, str]]):
        self.sitemap_url = sitemap_url
        self.catalog = base_catalog # initialize with the basic info
    
    def get_all_urls(self) -> list[str]:
        try:
            with httpx.Client(timeout = 10, # if the Agno website is temporarily down
                          follow_redirects = True) as client:
                response = client.get(self.sitemap_url)
                response.raise_for_status()
                sitemap_xml_content = response.text
                sitemap_soup = BeautifulSoup(sitemap_xml_content,
                                             features = "xml") # requires pip install lxml
                all_urls = [loc_tag.text for loc_tag in sitemap_soup.find_all("loc")]
                return all_urls
                
        except httpx.HTTPStatusError as exc:
            print(f"ERROR: impossible to scrape the sitemap {self.sitemap_url}: HTTP error {exc.response.status_code}")
            return [""]
        except Exception as exc:
            print(f"ERROR: impossible to scrape the sitemap {self.sitemap_url}: {exc}")
            return [""]

    def get_all_slugs(self) -> list[str]:
        all_urls = self.get_all_urls()
        all_slugs = [get_slug_from_url(url) for url in all_urls]
        return all_slugs

    def build_catalog(self) -> list[dict[str, str]]:
        all_urls = self.get_all_urls()
        
        for url in all_urls:
            slug = get_slug_from_url(url)
            if slug in [item["title"] for item in self.catalog]: # use slug and not url because it is shorter
                continue
            self.catalog.append({"title": slug, "url": url, "description": ""})
        return self.catalog

# catalog = AgnoDocumentationCatalog(SITEMAP_URL, BASE_CATALOG)
# populated_catalog = catalog.build_catalog()
###################################################################################
###################################### CACHE ######################################
###################################################################################

# we implement a cache system to avoid scraping the same page multiple times.

class AgnoDocumentationCache:
    def __init__(self):
        self.cache: dict[str, str] = {} # key: url, value: content
    
    def get_content(self, url: str) -> str:
        if url in self.cache:
            return self.cache[url]
        else:
            return ""
    
    def add_content(self, url: str, content: str) -> None:
        self.cache[url] = content
    
    