"""
email_scraper.py
----------------
Scrapes email addresses from an organisation's website.
Used to enrich NGO records that have a website URL but no email in OSM/Geoapify data.

Scraping strategy (in order):
  1. Check <a href="mailto:..."> links  — most reliable
  2. Regex scan visible text and meta tags
  3. Check /contact, /about, /about-us pages if homepage has no email
"""

import re
import logging
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 CareEquity/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 8  # seconds per request
CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/get-help"]

# Email regex — conservative, avoids false positives
EMAIL_RE = re.compile(
    r"\b([a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,253}\.[a-zA-Z]{2,10})\b"
)

# Domains to exclude — CDN/asset false positives and common trackers
SKIP_DOMAINS = {
    "sentry.io", "google.com", "facebook.com", "twitter.com",
    "instagram.com", "w3.org", "schema.org", "apple.com",
    "microsoft.com", "cloudflare.com", "amazonaws.com",
    "wix.com", "squarespace.com", "wordpress.com", "godaddy.com",
    "example.com", "domain.com", "yourdomain.com",
    "email.com", "mail.com",
}
SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".js", ".css",
    ".woff", ".woff2", ".svg", ".ico", ".mp4", ".pdf",
)


def _is_valid_email(email: str) -> bool:
    """Filter out obvious false positives."""
    email = email.lower().strip()
    if not email or "@" not in email:
        return False
    local, domain = email.rsplit("@", 1)
    if domain in SKIP_DOMAINS:
        return False
    if any(email.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if len(local) < 2 or len(domain) < 4:
        return False
    # Reject things like "1.0@..." version strings
    if re.match(r"^\d+\.\d+", local):
        return False
    return True


def _extract_emails_from_html(html: str) -> list[str]:
    """Extract and deduplicate valid emails from HTML content."""
    # Priority: mailto links first
    mailto_re = re.compile(r'href=["\']mailto:([^"\'\s?]+)', re.IGNORECASE)
    emails = mailto_re.findall(html)

    # Then text scan
    emails += EMAIL_RE.findall(html)

    seen = set()
    result = []
    for e in emails:
        e = e.lower().strip().rstrip(".")
        if e not in seen and _is_valid_email(e):
            seen.add(e)
            result.append(e)
    return result


def _fetch_html(url: str) -> str:
    """Fetch a page and return its HTML, or empty string on failure."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                         allow_redirects=True)
        if r.status_code == 200 and "text" in r.headers.get("Content-Type", ""):
            return r.text
    except requests.RequestException as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
    return ""


def scrape_email_from_website(url: str) -> str:
    """
    Attempt to find a contact email address on an organisation's website.

    Parameters
    ----------
    url : str
        The organisation's homepage URL.

    Returns
    -------
    str
        First valid email found, or empty string if none found.
    """
    if not url or not url.startswith(("http://", "https://")):
        return ""

    # Normalise URL
    parsed = urlparse(url)
    base   = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Try homepage
    html = _fetch_html(url)
    if html:
        emails = _extract_emails_from_html(html)
        if emails:
            logger.debug("Found email on homepage of %s: %s", url, emails[0])
            return emails[0]

    # 2. Try /contact and /about pages
    for path in CONTACT_PATHS:
        contact_url = urljoin(base, path)
        if contact_url == url:
            continue
        html = _fetch_html(contact_url)
        if html:
            emails = _extract_emails_from_html(html)
            if emails:
                logger.debug("Found email on %s: %s", contact_url, emails[0])
                return emails[0]

    logger.debug("No email found on website: %s", url)
    return ""


def enrich_orgs_with_emails(orgs: list[dict], max_scrape: int = 10) -> list[dict]:
    """
    For each org in *orgs* that has a website but no email,
    scrape the website to find an email address.

    Parameters
    ----------
    orgs : list[dict]
        List of org dicts (must have 'website' and 'email' keys).
    max_scrape : int
        Maximum number of websites to scrape (to stay within time budget).

    Returns
    -------
    list[dict]
        Same list with 'email' fields filled in where found.
    """
    scraped = 0
    for org in orgs:
        if scraped >= max_scrape:
            break
        if (org.get("email") or "").strip():
            continue  # already has email
        web = (org.get("website") or "").strip()
        if not web:
            continue
        email = scrape_email_from_website(web)
        if email:
            org["email"]  = email
            org["source"] = org.get("source", "") + " (email scraped)"
            logger.info("Scraped email for %s: %s", org.get("name",""), email)
        scraped += 1
    return orgs


# ── CLI test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.lafoodbank.org"
    email = scrape_email_from_website(url)
    print(f"Email found: {email!r}" if email else "No email found")
