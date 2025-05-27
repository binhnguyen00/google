import json;

from GoogleSearch import GoogleSearch, SearchResult;

def search():
  google = GoogleSearch(lang="vi", region="vn", safe="off", timeout=10)
  region: str = "hải dương"
  term: str = f"báo mới {region}"
  print(f"Term: {term}")
  results: list[SearchResult] = google.search(
    term=term,
    tbs="qdr:d",
    advanced=True,
    num_results=10,
    unique=True,
    start_num=0,
  )
  for result in results:
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))

def run():
  search()

if __name__ == "__main__":
  run()