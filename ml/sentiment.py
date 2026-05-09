from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from data.news import get_market_news
from data.cache import cache_get, cache_set

analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> dict:
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    label = (
        "POSITIVE" if compound >= 0.05 else
        "NEGATIVE" if compound <= -0.05 else
        "NEUTRAL"
    )
    return {"compound": round(compound, 4), "label": label}


def get_ticker_sentiment(ticker: str) -> dict:
    cache_key = f"sentiment:{ticker}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Clean up ticker for news search
    clean_ticker = ticker.replace(".NS", "").replace(".BO", "")
    articles = get_market_news(query=clean_ticker, page_size=10)

    if not articles or (len(articles) == 1 and articles[0]["url"] == "#"):
        return {
            "ticker": ticker,
            "overall": "NEUTRAL",
            "score": 0,
            "articles_scored": 0,
            "breakdown": {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0},
        }

    scores = []
    breakdown = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    scored_articles = []

    for article in articles:
        text = f"{article['title']} {article.get('description', '')}"
        score = score_text(text)
        scores.append(score["compound"])
        breakdown[score["label"]] += 1
        scored_articles.append({
            "title":     article["title"],
            "source":    article["source"],
            "published": article["published"],
            "sentiment": score["label"],
            "score":     score["compound"],
            "url":       article["url"],
        })

    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    overall = (
        "POSITIVE" if avg_score >= 0.05 else
        "NEGATIVE" if avg_score <= -0.05 else
        "NEUTRAL"
    )

    result = {
        "ticker":          ticker,
        "overall":         overall,
        "score":           avg_score,
        "articles_scored": len(scores),
        "breakdown":       breakdown,
        "articles":        scored_articles,
    }

    cache_set(cache_key, result)
    return result