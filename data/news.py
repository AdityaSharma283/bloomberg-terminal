import requests
from config import NEWS_API_KEY
from data.cache import cache_get, cache_set

def get_market_news(query: str = "stock market", page_size: int = 10) -> list:
    cached = cache_get(f"news:{query}")
    if cached:
        return cached

    if not NEWS_API_KEY:
        return _fallback_news()

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "language": "en",
            "apiKey": NEWS_API_KEY,
        }
        res = requests.get(url, params=params, timeout=5)
        articles = res.json().get("articles", [])
        result = [
            {
                "title": a["title"],
                "source": a["source"]["name"],
                "url": a["url"],
                "published": a["publishedAt"][:10],
                "description": a.get("description", ""),
            }
            for a in articles if a.get("title")
        ]
        cache_set(f"news:{query}", result)
        return result
    except Exception:
        return _fallback_news()


def _fallback_news() -> list:
    return [
        {"title": "Add your NewsAPI key in .env to see live news", "source": "System", "url": "#", "published": "", "description": ""},
    ]