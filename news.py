"""
StockScope AI - News Retrieval & Sentiment Analysis Module
Retrieves verified public market headlines from Yahoo Finance news feed
and applies a transparent financial lexicon sentiment classifier.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import yfinance as yf
from src.utils import sanitize_ticker

# Specialized financial sentiment lexicon
POSITIVE_WORDS = {
    "surge", "surges", "surged", "rally", "rallies", "rallied", "gain", "gains",
    "gained", "bullish", "jump", "jumps", "jumped", "growth", "profit", "profits",
    "profitable", "boost", "boosts", "boosted", "soar", "soars", "soared", "record",
    "high", "upgrade", "upgrades", "upgraded", "dividend", "outperform", "beat",
    "beats", "strong", "positive", "expand", "expansion", "rebound", "rise", "rises"
}

NEGATIVE_WORDS = {
    "plunge", "plunges", "plunged", "drop", "drops", "dropped", "fall", "falls",
    "fell", "decline", "declines", "declined", "bearish", "loss", "losses", "crash",
    "crashes", "crashed", "slump", "slumps", "slumped", "cut", "cuts", "downgrade",
    "downgraded", "downgrades", "warning", "warns", "warned", "debt", "risk",
    "default", "weak", "negative", "investigation", "probe", "fraud", "penalty", "low"
}


def analyze_headline_sentiment(title: str) -> Dict[str, Any]:
    """
    Score financial headline sentiment using transparent keyword analysis.
    Returns: (sentiment_label, score, pos_words, neg_words)
    """
    words = title.lower().replace(",", " ").replace(".", " ").replace("'", "").split()
    pos_matches = [w for w in words if w in POSITIVE_WORDS]
    neg_matches = [w for w in words if w in NEGATIVE_WORDS]

    score = len(pos_matches) - len(neg_matches)

    if score > 0:
        sentiment = "Positive"
        badge = "🟢 Positive"
    elif score < 0:
        sentiment = "Negative"
        badge = "🔴 Negative"
    else:
        sentiment = "Neutral"
        badge = "⚪ Neutral"

    return {
        "sentiment": sentiment,
        "badge": badge,
        "score": score,
        "positive_terms": pos_matches,
        "negative_terms": neg_matches,
    }


def fetch_stock_news(ticker: str, max_items: int = 8) -> List[Dict[str, Any]]:
    """
    Fetch recent market news for a ticker via yfinance.
    Gracefully handles empty responses and network failures.
    """
    clean_sym = sanitize_ticker(ticker)
    if not clean_sym:
        return []

    try:
        t = yf.Ticker(clean_sym)
        raw_news = getattr(t, "news", [])
        if not raw_news or not isinstance(raw_news, list):
            return []

        processed_news = []
        for item in raw_news[:max_items]:
            title = item.get("title", "")
            publisher = item.get("publisher", "Market Wire")
            link = item.get("link", "#")
            pub_time = item.get("providerPublishTime")

            if pub_time:
                try:
                    pub_str = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pub_str = "Recent"
            else:
                pub_str = "Recent"

            sentiment_data = analyze_headline_sentiment(title)

            processed_news.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "published_at": pub_str,
                "sentiment": sentiment_data["sentiment"],
                "badge": sentiment_data["badge"],
                "score": sentiment_data["score"],
            })

        return processed_news
    except Exception:
        # Offline or feed rate-limited: return empty list without crashing
        return []
