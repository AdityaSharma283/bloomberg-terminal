import requests
from config import FRED_API_KEY
from data.cache import cache_get, cache_set

FRED_SERIES = {
    "US_GDP_GROWTH":     "A191RL1Q225SBEA",
    "US_CPI":            "CPIAUCSL",
    "US_UNEMPLOYMENT":   "UNRATE",
    "FED_FUNDS_RATE":    "FEDFUNDS",
    "US_10Y_YIELD":      "GS10",
    "US_2Y_YIELD":       "GS2",
    "VIX":               "VIXCLS",
    "US_RETAIL_SALES":   "RSAFS",
}

def get_fred_series(series_id: str, limit: int = 12) -> list:
    if not FRED_API_KEY or FRED_API_KEY == "":
        return []
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id":     series_id,
            "api_key":       FRED_API_KEY,
            "file_type":     "json",
            "sort_order":    "desc",
            "limit":         limit,
        }
        res = requests.get(url, params=params, timeout=5)
        obs = res.json().get("observations", [])
        return [
            {"date": o["date"], "value": float(o["value"]) if o["value"] != "." else None}
            for o in obs if o["value"] != "."
        ]
    except:
        return []


def get_macro_dashboard() -> dict:
    cached = cache_get("macro_dashboard")
    if cached:
        return cached

    result = {}
    for name, series_id in FRED_SERIES.items():
        data = get_fred_series(series_id, limit=2)
        if data:
            latest = data[0]
            prev   = data[1] if len(data) > 1 else None
            change = round(latest["value"] - prev["value"], 3) if prev and latest["value"] and prev["value"] else None
            result[name] = {
                "value":  latest["value"],
                "date":   latest["date"],
                "change": change,
            }
        else:
            result[name] = {"value": None, "date": None, "change": None}

    # Yield curve
    if result.get("US_10Y_YIELD", {}).get("value") and result.get("US_2Y_YIELD", {}).get("value"):
        spread = round(result["US_10Y_YIELD"]["value"] - result["US_2Y_YIELD"]["value"], 3)
        result["YIELD_CURVE_SPREAD"] = {
            "value": spread,
            "date":  result["US_10Y_YIELD"]["date"],
            "change": None,
            "inverted": spread < 0,
        }

    cache_set("macro_dashboard", result)
    return result