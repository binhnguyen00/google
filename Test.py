import json;

from GoogleSearch import GoogleSearch, SearchResult;

def search():
  google = GoogleSearch(lang="vi", region="vn", safe="off", timeout=10)
  region: str = "hải dương"
  search_query: str = f"báo mới {region}"
  print(f"Search Query: {search_query}")
  results: list[SearchResult] = google.search(
    query=search_query,
    date_range="d",
    desire="news",
    num_results=2,
    start_num=0,
    unique=True,
  )
  for result in results:
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))

def run():
  search()

if __name__ == "__main__":
  run()