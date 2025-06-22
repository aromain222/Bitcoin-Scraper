import json
from urllib.parse import quote_plus
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser as date_parser  # type: ignore

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
SEARCH_URL = "https://www.google.com/search"
DEFAULT_QUERY = "bitcoin grants"


# Pre-compiled regex to capture USD amounts like "$100,000" or "$1.5M".
DOLLAR_RE = re.compile(r"\$\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?(?:\s?[mkMK])?)")

# Simple sector keyword mapping. Expand as desired.
SECTOR_KEYWORDS: dict[str, list[str]] = {
    # User-defined sector taxonomy
    "ARBITURE OF TRUTH": [
        "arbiter of truth",
        "arbiters of truth",
        "arbiture of truth",
        "disinformation",
        "fact check",
    ],
    "CO-WORKING/EVENT SPACE": [
        "coworking",
        "co-working",
        "co working",
        "event space",
        "meetup venue",
        "shared office",
    ],
    "DATA/TRANSPARANCY": [
        "data transparency",
        "open data",
        "analytics",
        "transparency",
    ],
    "EDUCATION/MEDIA": [
        "education",
        "educational",
        "training",
        "tutorial",
        "media",
        "podcast",
        "journalism",
    ],
    "EXCHANGE": [
        "exchange",
        "trading platform",
        "crypto exchange",
        "swap",
    ],
    "FINANCIAL SERVICES": [
        "financial service",
        "fintech",
        "banking",
        "payments",
        "remittance",
    ],
    "HARDWARE (MINING)": [
        "mining hardware",
        "asic miner",
        "mining rig",
        "drillbit",
    ],
    "HARDWARE (SELF-SOVERIEGN)": [
        "hardware wallet",
        "self-sovereign hardware",
        "coldcard",
        "trezor",
        "ledger",
    ],
    "MINING": [
        "bitcoin mining",
        "mining",
        "hashrate",
        "mine bitcoin",
    ],
    "MINING POOL": [
        "mining pool",
        "pool operator",
        "hash pool",
    ],
    "SCALING SOLUTION": [
        "scaling solution",
        "layer2",
        "layer 2",
        "sidechain",
        "rollup",
        "lightning network",
    ],
    "SOFTWARE (SELF-SOVERIGN)": [
        "self-sovereign software",
        "self custodial",
        "wallet software",
        "full node",
        "sovereign stack",
    ],
    "HEAT REUSE": [
        "heat reuse",
        "waste heat",
        "heat recycling",
        "immersion cooling",
    ],
    "LAYER 1 DEVELOPMENT": [
        "layer 1",
        "core development",
        "core dev",
        "protocol dev",
        "consensus",
    ],
}


def search_google(query: str, max_results: int = 20) -> list[dict]:
    """Return a list of Google Search results.

    Note: Scraping Google directly may violate their terms of service and
    trigger anti-bot protections. For production use, consider the Google
    Custom Search API or a third-party service. This simple parser should
    suffice for quick, lightweight experimentation.
    """
    params = {"q": query, "num": str(max_results), "hl": "en"}
    headers = {"User-Agent": USER_AGENT}

    response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict] = []

    # Google results are typically within <div class="tF2Cxc"> or <div class="g"> blocks.
    for result_block in soup.select("div.tF2Cxc, div.yuRUbf"):
        a_tag = result_block.find("a", href=True)
        title_tag = result_block.find("h3")
        if not a_tag or not title_tag:
            continue
        url = a_tag["href"]
        title = title_tag.get_text(strip=True)
        if url and title:
            results.append({"title": title, "url": url})
        if len(results) >= max_results:
            break

    return results


def identify_sector(text: str) -> str | None:
    """Return the first matching sector based on keyword heuristics."""
    lowered = text.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return sector
    return None


def extract_grant_info(url: str, timeout: int = 10) -> dict:
    """Fetch the page at `url` and attempt to extract grant details.

    Returns a dict with keys: `url`, `amount`, `sector`, `company`.
    Missing values may be None.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:
        return {"url": url, "error": str(exc)}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract page text for searching.
    page_text = soup.get_text(" ", strip=True)

    # Amount extraction.
    amount_match = DOLLAR_RE.search(page_text)
    amount = amount_match.group(0) if amount_match else None

    # Sector extraction.
    sector = identify_sector(page_text)

    # Company extraction: try meta tags then fallback to domain.
    company = None
    meta_site_name = soup.find("meta", property="og:site_name")
    if meta_site_name and meta_site_name.get("content"):
        company = meta_site_name["content"].strip()
    if not company:
        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            company = meta_title["content"].strip().split("|")[0]
    if not company:
        domain = urlparse(url).netloc
        company = domain.replace("www.", "")

    # Date extraction.
    published_date: str | None = None

    def _try_parse_date(raw: str | None) -> str | None:
        if not raw:
            return None
        try:
            dt = date_parser.parse(raw, fuzzy=True)
            if dt:
                return dt.date().isoformat()
        except Exception:
            pass
        return None

    # Common meta tags for published time.
    for meta_name in [
        ("property", "article:published_time"),
        ("property", "og:published_time"),
        ("itemprop", "datePublished"),
        ("name", "date"),
    ]:
        key, value = meta_name
        tag = soup.find("meta", {key: value})
        if tag and tag.get("content"):
            published_date = _try_parse_date(tag["content"])
            if published_date:
                break

    # Fallback: search JSON-LD scripts for datePublished.
    if not published_date:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json as _json

                data = _json.loads(script.string or "{}")
                if isinstance(data, dict):
                    date_str = data.get("datePublished") or data.get("dateCreated")
                    published_date = _try_parse_date(date_str)
                    if published_date:
                        break
            except Exception:
                continue

    # Very fuzzy regex fallback (e.g., "January 2023")
    if not published_date:
        month_names = "January|February|March|April|May|June|July|August|September|October|November|December"
        regex = re.compile(rf"\b({month_names})\s+\d{{1,2}},?\s+\d{{4}}", re.IGNORECASE)
        match = regex.search(page_text)
        if match:
            published_date = _try_parse_date(match.group(0))

    year_val = None
    if published_date:
        try:
            year_val = datetime.fromisoformat(published_date).year
        except Exception:
            year_val = None

    return {
        "url": url,
        "amount": amount,
        "sector": sector,
        "company": company,
        "date": published_date,
        "year": year_val,
    }


def main() -> None:
    """Entry point for the script."""
    query = DEFAULT_QUERY
    results = search_google(query)

    # Concurrently process each result to extract grant info.
    enriched: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(extract_grant_info, r["url"]): r for r in results}
        for future in as_completed(future_to_url):
            info = future.result()
            enriched.append(info)

    print(json.dumps(enriched, indent=2))


if __name__ == "__main__":
    main() 