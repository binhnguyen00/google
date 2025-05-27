import time;
import requests

from typing import List, Optional, Set;
from urllib.parse import unquote;
from bs4 import BeautifulSoup;
from UserAgent import get_useragent;

class SearchResult():
  """
  Container for a single search result.
  """
  def __init__(self, url: str, title: str, description: str) -> None:
    self.url: str = url
    self.title: str = title
    self.description: str = description

  def __repr__(self) -> str:
    return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"


class GoogleSearch():
  """
  A simple interface to fetch Google search results.
  """

  BASE_URL = "https://www.google.com/search"

  def __init__(
    self,
    lang: str = "vi",
    safe: str = "active",
    region: Optional[str] = "vn",
    timeout: int = 5,
    ssl_verify: Optional[bool] = True,
    proxy: Optional[str] = None,
    sleep_interval: float = 0,
  ) -> None:
    self.lang = lang
    self.safe = safe
    self.region = region
    self.timeout = timeout
    self.ssl_verify = ssl_verify
    self.sleep_interval = sleep_interval
    self.session = requests.Session()
    if proxy:
      proxy_dict = {"http": proxy, "https": proxy}
      self.session.proxies.update(proxy_dict)

  def _build_params(self, query: str, num: int, start: int, tbs: str) -> dict:
    params = {
      "q": query,
      "num": num,
      "hl": self.lang,
      "safe": self.safe,
      "start": start,
      "tbs": tbs,
    }
    if self.region:
      params["gl"] = self.region
    return params

  def _request(self, params: dict) -> requests.Response:
    resp = self.session.get(
      url=self.BASE_URL,
      headers={
        "User-Agent": get_useragent(),
        "Accept": "*/*"
      },
      params=params,
      timeout=self.timeout,
      verify=self.ssl_verify,
      cookies = {
        'CONSENT': 'PENDING+987', # bypasses the consent page
        'SOCS': 'CAESHAgBEhIaAB',
      }
    )
    resp.raise_for_status()
    return resp

  def search(self, term: str, num_results: int = 10, tbs: str = "qdr:w", start_num: int = 0, unique: bool = False, advanced: bool = False) -> List[SearchResult]:
    """
    Perform a Google search and return a list of results.
    Example usage:
    searcher = GoogleSearcher(region='US', sleep_interval=1)
    results = searcher.search("example query", num_results=5, advanced=True)
    for r in results:
      print(r)

    Args:
      term: query string
      num_results: number of results to return
      tbs: time filter for results (e.g., 'qdr:w')
      start_num: pagination offset
      unique: enforce unique URLs
      advanced: if True, include title and description in SearchResult; otherwise only URLs in SearchResult.url

    Returns:
      A list of SearchResult objects
    """
    results: List[SearchResult] = []
    fetched: int = 0
    seen: Set[str] = set()
    start: int = start_num

    while fetched < num_results:
      batch = num_results - fetched
      params = self._build_params(term, batch + 2, start, tbs)
      resp = self._request(params=params)
      soup = BeautifulSoup(resp.text, "html.parser")
      blocks = soup.select("div.ezO2md")
      new_found: int = 0

      for block in blocks:
        link_tag = block.find("a", href=True)
        title_tag = link_tag.find("span", class_="CVA68e") if link_tag else None # type: ignore
        desc_tag = block.find("span", class_="FrIlee")

        if not (link_tag and title_tag and desc_tag):
          continue

        raw_href: str = link_tag["href"] # type: ignore
        url = unquote(raw_href.split("&")[0].replace("/url?q=", ""))

        if unique and url in seen:
          continue

        seen.add(url)
        title = title_tag.get_text(strip=True) if advanced else ""
        description = desc_tag.get_text(strip=True) if advanced else ""

        results.append(SearchResult(url, title, description))
        fetched += 1
        new_found += 1

        if fetched >= num_results:
          break

      if new_found == 0:
        break

      start += 10
      if self.sleep_interval > 0:
        time.sleep(self.sleep_interval)

    return results