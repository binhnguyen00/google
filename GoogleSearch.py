import time;
import requests;

from requests import Response;
from typing import List, Literal, Optional, Set;
from urllib.parse import unquote;
from bs4 import BeautifulSoup, Tag;
from sentence_transformers import SentenceTransformer, util;

from .UserAgent import get_useragent;

class SearchResult():
  """ Google search result
    url: str
    title: str
    description: str
  """
  url: str
  title: str
  description: str
  def __init__(self, url: str, title: str, description: str) -> None:
    self.url: str = url
    self.title: str = title
    self.description: str = description

class GoogleSearch():
  BASE_URL = "https://www.google.com/search"

  def __init__(
    self,
    lang: str = "vi",
    safe: Literal["active", "off"] = "off",
    region: Optional[str] = "vn",
    timeout: int = 5,
    ssl_verify: Optional[bool] = True,
    proxy: Optional[str] = None,
    sleep_interval: float = 1,
  ) -> None:
    self.lang = lang
    self.safe = safe
    self.region = region
    self.timeout = timeout
    self.ssl_verify = ssl_verify
    self.sleep_interval = sleep_interval
    self.session = requests.Session()
    if (proxy):
      self.session.proxies.update({ 
        "http": proxy, 
        "https": proxy 
      })

  def _build_params(
    self,
    query: str,
    num: int,
    start: int,
    qdr: Literal['d', 'w', 'm', 'y'] = 'w',
    tbm: Literal['news', 'images', 'videos', 'shop', 'all'] = 'all',
  ) -> dict:
    """ Build the parameters for the Google search request. """
    tbm_map = {
      "news": "nws",
      "images": "isch",
      "videos": "vid",
      "shop": "shop",
      "all": "all",
    }
    to_be_match = tbm_map.get(tbm, "all")
    to_be_sort = "sbd:1" if qdr == "d" else f"qdr:{qdr}"
    params = {
      "q"     : query,
      "num"   : num,
      "hl"    : self.lang,
      "gl"    : self.region,
      "safe"  : self.safe,
      "start" : start,
      "tbs"   : to_be_sort,
      "tbm"   : to_be_match,
    }
    if (to_be_match == 'all'): del params["tbm"] # search all
    return params

  def _send_request(self, params: dict) -> Response:
    resp = self.session.get(
      url=self.BASE_URL,
      headers={
        "User-Agent": get_useragent(),
        "Accept": "*/*"
      },
      params=params,
      timeout=self.timeout,
      verify=self.ssl_verify,
      # cookies = {
      #   'CONSENT': 'PENDING+987', # bypasses the consent page
      #   'SOCS': 'CAESHAgBEhIaAB',
      # }
    )
    resp.raise_for_status()
    return resp

  def _filter(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
    """ use pre-trained model to filter out irrelevant results """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query, convert_to_tensor=True)
    for idx, result in enumerate(results):
      text: str = f"{result.title} {result.description}"
      text_embedding = model.encode(text, convert_to_tensor=True)
      threshold: float = 0.3
      similarity: float = util.pytorch_cos_sim(query_embedding, text_embedding).item()
      if (similarity < threshold):
        results.pop(idx)

    return results

  def search(self,
    query: str,
    num_results: int = 10,
    date_range: Literal['d', 'w', 'm', 'y'] = 'w',
    desire: Literal['news', 'images', 'videos', 'shop', 'all'] = 'all',
    start_num: int = 0,
    unique: bool = True,
  ) -> List[SearchResult]:
    """
    Perform a Google search and return a list of results.
    Example usage:
    searcher = GoogleSearch(region='US', sleep_interval=1)
    results = searcher.search("example query", num_results=5)
    for r in results:
      print(r)

    Args:
      query       : what to search
      num_results : number of results to return
      date_range  : query date range for results (e.g., 'd', 'w', 'm', 'y')
      start_num   : pagination offset
      unique      : enforce unique URLs
      desire      : type of results

    Returns:
      A list of SearchResult objects
    """
    results: List[SearchResult] = []
    fetched: int = 0
    seen: Set[str] = set()
    start: int = start_num

    while (fetched < num_results):
      batch: int          = num_results - fetched
      params: dict        = self._build_params(query=query, num=batch + 2, start=start, qdr=date_range, tbm=desire)
      resp: Response      = self._send_request(params=params)
      soup: BeautifulSoup = BeautifulSoup(resp.text, "html.parser")
      blocks: list[Tag]   = soup.select("div.ezO2md")
      new_found: int      = 0

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
        title = title_tag.get_text(strip=True) or ""
        description = desc_tag.get_text(strip=True) or ""

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

    results = self._filter(query=query, results=results)
    return results