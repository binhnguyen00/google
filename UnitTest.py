import json;

from .GoogleSearch import GoogleSearch, SearchResult;

def search():
  google = GoogleSearch(lang="vi", region="vn", timeout=10)
  region: str = "hải phòng"
  concern: str = "an toàn giao thông"
  search_query: str = f"{concern} ở {region}"
  print(f"Search Query: {search_query}")
  results: list[SearchResult] = google.search(
    query=search_query,
    date_range="d",
    desire="news",
    num_results=3,
    start_num=0,
    unique=True,
  )
  for result in results:
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))

def run():
  search()

if __name__ == "__main__":
  run()