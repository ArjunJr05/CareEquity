"""
bot.py  —  NVIDIA-powered SDoH Intelligence Bot
=================================================
"""

import os, re, sys, json, hashlib
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
PRIMARY_MODEL   = "meta/llama-3.1-8b-instruct"
FALLBACK_MODEL  = "meta/llama-3.1-70b-instruct"

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
try:
    from mcp_client import search_pubmed_sync   # type: ignore
except Exception as _mcp_err:
    def search_pubmed_sync(query: str, max_results: int = 3) -> str:
        return "PubMed MCP unavailable."

# ── CSV for FIPS lookup ────────────────────────────────────────────
import pandas as _pd
_CSV_PATH  = os.path.join(os.path.dirname(__file__), "src", "SDOH_MODEL_DATA.csv")
_county_df = None

def _get_county_df():
    global _county_df
    if _county_df is None:
        try:
            _county_df = _pd.read_csv(_CSV_PATH, dtype={"county_fips": str})
        except Exception:
            _county_df = _pd.DataFrame()
    return _county_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — ChromaDB Citation Cache
# ══════════════════════════════════════════════════════════════════════════════

_chroma_client     = None
_citation_cache    = None
_CACHE_DIR         = os.path.join(os.path.dirname(__file__), ".chroma_cache")
_SIMILARITY_THRESH = 0.72   # cosine similarity — above this = cache hit


def _get_cache():
    """
    Lazy-init ChromaDB. Import happens here (not at module load) so that
    FastAPI can import bot.py without triggering the ONNX model download.
    """
    global _chroma_client, _citation_cache
    if _citation_cache is not None:
        return _citation_cache
    try:
        import chromadb as _chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction as _DEF
        _chroma_client  = _chromadb.PersistentClient(path=_CACHE_DIR)
        _citation_cache = _chroma_client.get_or_create_collection(
            name="sdoh_citations",
            embedding_function=_DEF(),
            metadata={"hnsw:space": "cosine"},
        )
        _purge_test_articles(_citation_cache)
    except Exception:
        _citation_cache = None
    return _citation_cache


def _purge_test_articles(col):
    """Remove fake/test articles that should never appear in production."""
    _FAKE_PMIDS = {"99999999", "12345678", "00000000"}
    try:
        for pmid in _FAKE_PMIDS:
            doc_id = hashlib.md5(pmid.encode()).hexdigest()
            try:
                col.delete(ids=[doc_id])
            except Exception:
                pass
    except Exception:
        pass


def _cache_lookup(query: str) -> list[dict] | None:
    """
    Search the local ChromaDB cache for articles relevant to `query`.
    Returns a list of article dicts if a good match is found, else None.
    """
    col = _get_cache()
    if col is None or col.count() == 0:
        return None
    try:
        res = col.query(query_texts=[query], n_results=min(3, col.count()),
                        include=["documents", "metadatas", "distances"])
        distances  = res["distances"][0]   # cosine distance; 0 = identical
        metadatas  = res["metadatas"][0]
        # Convert distance → similarity  (chromadb cosine: 0=same, 2=opposite)
        sims = [1 - (d / 2) for d in distances]
        hits = [m for m, s in zip(metadatas, sims) if s >= _SIMILARITY_THRESH]
        if hits:
            return [json.loads(h["article_json"]) for h in hits]
    except Exception:
        pass
    return None


def _cache_store(query: str, articles: list[dict]):
    """Store newly fetched articles in ChromaDB keyed by query."""
    col = _get_cache()
    if col is None or not articles:
        return
    try:
        for a in articles:
            doc_id = hashlib.md5(a["pmid"].encode()).hexdigest()
            # Store the article JSON in metadata; document = title for embedding
            col.upsert(
                ids=[doc_id],
                documents=[f"{a['title']} {query}"],   # embedded text
                metadatas=[{"article_json": json.dumps(a), "factor": query}],
            )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TASK 4 — Language Detection
# ══════════════════════════════════════════════════════════════════════════════

try:
    from langdetect import detect as _ld_detect
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False

# Maps langdetect codes → human-readable language name for the prompt
_LANG_NAMES = {
    "ta": "Tamil",   "hi": "Hindi",    "te": "Telugu",
    "kn": "Kannada", "ml": "Malayalam","mr": "Marathi",
    "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi",
    "fr": "French",  "de": "German",   "es": "Spanish",
    "zh-cn": "Chinese", "ja": "Japanese", "ar": "Arabic",
    "en": "English",
}

def _detect_language(text: str) -> str:
    """
    Return a language name like 'Tamil', 'Hindi', 'English'.
    For Romanized Indian languages (typed in English letters),
    we use a keyword pattern since langdetect cannot distinguish them.
    """
    # Romanized Tamil keyword patterns (common transliterations)
    _TAMIL_ROMAN = {
        "panalam","pannalam","sollu","seyalam","enna","yenga","epadi",
        "parunga","solunga","theriyuma","illai","aamaa","eppo","yenna",
        "lam","la","pa","ma", "pom", "ponga", "vaanga",
    }
    # Romanized Hindi keyword patterns
    _HINDI_ROMAN = {
        "kya","karo","kaise","batao","dijiye","chahiye","hain","mein",
        "aur","nahi","hai","tha","kar","ke","ki","ka",
    }
    words = set(re.findall(r"\b\w+\b", text.lower()))

    # Check for Romanized Tamil first (higher priority)
    if len(words & _TAMIL_ROMAN) >= 2:
        return "Tamil"
    # Check for Romanized Hindi
    if len(words & _HINDI_ROMAN) >= 2:
        return "Hindi"

    # Unicode-script based detection — Devanagari = Hindi
    if re.search(r"[\u0900-\u097F]", text):
        return "Hindi"
    # Tamil script
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "Tamil"

    # Fall back to langdetect for other languages
    if not _LANGDETECT_AVAILABLE or not text.strip():
        return "English"
    try:
        code = _ld_detect(text)
        # Don't trust langdetect for short/mixed text — default to English
        if len(text.strip()) < 15:
            return "English"
        return _LANG_NAMES.get(code, "English")
    except Exception:
        return "English"


# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — Protective Factor Exclusion
# ══════════════════════════════════════════════════════════════════════════════

# These factors are GOOD when HIGH — never list them as risks
_PROTECTIVE_FACTORS = {
    "internet subscription rate",
    "grocery store density",
    "grocery store density (per 1k)",
}


# ── Intent classifier ─────────────────────────────────────────────────────────
_CARE_WORDS = {
    "treat","treatment","therapy","therapies","care","manage","management",
    "intervention","interventions","medicine","medication","drug","drugs",
    "cure","prevent","prevention","clinical","evidence","research",
    "pubmed","literature","journal","recommend","recommendation",
    "guideline","protocol","program","approach","reduce","address",
    "improve","strategies","strategy","help","how","what can",
    # Tamil / transliterated equivalents
    "panalam","pannalam","sollu","seyalam","enna","yenga","epadi",
}
_RISK_WORDS = {
    "risk","factor","factors","rate","prevalence","percentage","score",
    "poverty","unemployment","insecurity","food","housing","transport",
    "vehicle","insurance","obesity","diabetes","hypertension",
    "blood pressure","smoking","mental","physical","heart","svi",
    "vulnerability","index","county","compare","average","above",
    "below","highest","lowest","data","statistics","number","value",
    "show","list","what is","how high","how low",
    # Tamil
    "vilam","karanam","nilai","neela",
}

def classify_intent(question: str) -> str:
    """
    Classify the user's question into one of:
      greeting    — hi, hello, bye, thanks, casual chat
      fips_lookup — what is the county code / FIPS
      county_info — "my county", "my place", "what county"
      risk        — risk factors, data, prevalence questions
      care        — interventions, treatment, help questions
      mixed       — both risk + care aspects
    """
    q     = question.strip()
    ql    = q.lower()
    words = set(re.findall(r"\b\w+\b", ql))

    # ── Greeting / farewell / casual ────────────────────────────
    _GREET_PATTERNS = [
        r"^(hi|hello|hey|hii|hiii|hai|sup|yo)\b",
        r"^(bye|goodbye|see you|see ya|cya|later|ttyl|tata)\b",
        r"^(thanks|thank you|thx|ty|ok|okay|k|good|great|nice|cool|sure)\b",
        r"^(how are you|how r u|how do you do)\b",
        r"^\w{1,4}$",          # very short — 1-4 char messages like "k", "ok"
    ]
    for pat in _GREET_PATTERNS:
        if re.search(pat, ql):
            return "greeting"

    # ── FIPS / county code lookup ────────────────────────────────
    if re.search(r"\b(fips|county.?code|fips.?code|what.*(code|number|id))\b", ql, re.I):
        return "fips_lookup"

    # ── "My county / my place / my area" — user asking about selected county ─
    _MY_PATTERNS = [
        r"\bmy (county|place|area|region|location|contyu|contry|countu|coutny)\b",
        r"\bthis county\b",
        r"\bwhat (county|place|area) (is this|am i|are we)\b",
        r"\b(where am i|where are we)\b",
    ]
    for pat in _MY_PATTERNS:
        if re.search(pat, ql, re.I):
            return "county_info"

    # ── Care / intervention — include typo variants ──────────────
    _CARE_PATTERNS = [
        r"\b(care|cae|caer|carr|caare|carre|orivide|provide)\b",
        r"\b(interv|intervent|interventions?)\b",
        r"\b(treat|treatm|therapy|therapies)\b",
        r"\b(help|improve|reduce|address|prevent|program|program)\b",
        r"\b(what (can|should|to) (we|i|do|be))\b",
        r"\b(how (to|can|do|should))\b",
        r"\bpanalam\b|\bpannalam\b|\bseyalam\b",   # Tamil
    ]
    for pat in _CARE_PATTERNS:
        if re.search(pat, ql, re.I):
            # If question also has strong risk keywords, classify as mixed
            _RISK_STRONG = {"risk","factor","prevalence","rate","data","statistics",
                            "score","index","compare","average"}
            if words & _RISK_STRONG:
                return "mixed"
            return "care"

    # ── Risk / data questions ────────────────────────────────────
    _RISK_STRONG = {
        "risk","factor","factors","rate","prevalence","percentage","score",
        "poverty","unemployment","insecurity","food","housing","transport",
        "vehicle","insurance","obesity","diabetes","hypertension",
        "blood pressure","smoking","mental","physical","heart","svi",
        "vulnerability","index","compare","average","above","below",
        "highest","lowest","data","statistics","number","value",
        "show","list","affecting","impact","health",
    }
    if words & _RISK_STRONG:
        return "risk"

    # Default — treat unknown short messages as greetings, others as risk
    if len(words) <= 3:
        return "greeting"
    return "risk"


def _lookup_fips(county_context: str) -> str:
    """
    Extract county name + state from the context string,
    look it up in the CSV, and return a direct FIPS answer.
    """
    # Parse county name and state from context
    name_m  = re.search(r"County:\s*(.+),\s*([A-Z]{2})", county_context)
    if not name_m:
        return "I couldn't find the FIPS code — please check the county selected in the sidebar."

    county_name = name_m.group(1).strip()
    state_abbr  = name_m.group(2).strip()

    df = _get_county_df()
    if df.empty:
        return f"The FIPS code for {county_name}, {state_abbr} is not available (CSV not loaded)."

    # Match on county_name and state_abbr
    mask = (
        df["county_name"].str.contains(county_name.split(",")[0], case=False, na=False) &
        (df["state_abbr"].str.upper() == state_abbr.upper())
    )
    matches = df[mask]
    if matches.empty:
        return (f"Could not find FIPS code for **{county_name}, {state_abbr}** in the dataset. "
                f"Please verify the county name.")

    row  = matches.iloc[0]
    fips = str(row["county_fips"]).zfill(5)
    name = row["county_name"]
    return (
        f"**FIPS Code for {name}, {state_abbr}: `{fips}`**\n\n"
        f"You can use this code to look up the county in any federal dataset "
        f"(e.g. CDC PLACES, Census, HUD)."
    )


def _county_summary(county_context: str) -> str:
    """
    Return a concise one-card summary of the selected county
    when user asks 'my county', 'my place', 'where am I', etc.
    """
    name_m   = re.search(r"County:\s*(.+?),\s*([A-Z]{2})", county_context)
    pop_m    = re.search(r"Population:\s*([\d,]+)", county_context)
    inc_m    = re.search(r"Median Household Income:\s*(\$[\d,]+)", county_context)
    svi_m    = re.search(r"SVI Score:\s*([\d.]+)\s+\(([^)]+)\)", county_context)

    name  = name_m.group(1).strip() if name_m else "Selected County"
    state = name_m.group(2).strip() if name_m else ""
    pop   = pop_m.group(1) if pop_m else "N/A"
    inc   = inc_m.group(1) if inc_m else "N/A"
    svi   = f"{svi_m.group(1)} ({svi_m.group(2)})" if svi_m else "N/A"

    # FIPS from CSV
    df = _get_county_df()
    fips = "N/A"
    if not df.empty and name_m:
        mask = (
            df["county_name"].str.contains(name.split(",")[0], case=False, na=False) &
            (df["state_abbr"].str.upper() == state.upper())
        )
        rows = df[mask]
        if not rows.empty:
            fips = str(rows.iloc[0]["county_fips"]).zfill(5)

    return (
        f"**{name}, {state}**\n"
        f"- FIPS Code: `{fips}`\n"
        f"- Population: {pop}\n"
        f"- Median Income: {inc}\n"
        f"- Social Vulnerability: {svi}\n\n"
        f"Ask me about *risk factors*, *interventions*, or say **'provide care'** for recommendations."
    )


# ── Extract elevated factors — excluding protective ones ──────────────────────
def _extract_elevated_factors(county_context: str) -> list[str]:
    """
    Returns factors that are ABOVE US average, sorted by gap (largest first).
    Protective factors (high = good) are excluded entirely.
    """
    elevated = []
    for line in county_context.split("\n"):
        if "[ABOVE avg" not in line:
            continue
        m = re.match(r"\s*-\s*([^:]+):", line)
        if not m:
            continue
        factor_name = m.group(1).strip()
        # TASK 1 FIX: skip protective factors
        if factor_name.lower() in _PROTECTIVE_FACTORS:
            continue
        diff_m = re.search(r"\[ABOVE avg by ([\d.]+)", line)
        diff   = float(diff_m.group(1)) if diff_m else 0.0
        elevated.append((diff, factor_name))

    elevated.sort(key=lambda x: x[0], reverse=True)
    return [name for _, name in elevated]


# ── Factor → PubMed query map ─────────────────────────────────────────────────
_FACTOR_QUERY_MAP = {
    "poverty rate":                    "poverty community health intervention program outcomes",
    "unemployment rate":               "unemployment health outcomes community intervention program",
    "no vehicle rate":                 "lack vehicle transportation healthcare access intervention",
    "transportation barrier":          "transportation barrier rural healthcare access community",
    "lack of health insurance":        "uninsured low-income healthcare access community program",
    "food insecurity":                 "food insecurity community intervention nutrition outcomes",
    "housing insecurity":              "housing instability community health intervention outcomes",
    "low food access pct":             "food desert nutrition access community intervention",
    "snap low access pct":             "SNAP food assistance program health outcomes",
    "fast food density":               "fast food environment obesity prevention community",
    "diabetes prevalence":             "diabetes prevention community intervention low-income",
    "obesity prevalence":              "obesity prevention community-based intervention program",
    "high blood pressure prevalence":  "hypertension community-based blood pressure intervention",
    "physical inactivity":             "physical activity promotion community intervention program",
    "smoking prevalence":              "smoking cessation community intervention program",
    "heart disease prevalence":        "cardiovascular disease prevention community program",
    "poor mental health (14+ days)":   "mental health community intervention low-income program",
    "poor physical health (14+ days)": "chronic disease physical health community intervention",
}

def _query_for_factor(name: str) -> str:
    key = name.lower().strip()
    if key in _FACTOR_QUERY_MAP:
        return _FACTOR_QUERY_MAP[key]
    for k, v in _FACTOR_QUERY_MAP.items():
        if k in key or key in k:
            return v
    return f"{name} community health intervention program"


# ── PubMed result parser ───────────────────────────────────────────────────────
def _parse_pubmed_articles(raw: str) -> list[dict]:
    """Parse pubmedmcp output into structured article dicts."""
    if not raw or not raw.strip():
        return []
    if raw.strip().startswith("Error") or "No PubMed" in raw:
        return []

    raw    = raw.replace("\r\n", "\n").strip()
    blocks = re.split(r"\n(?=\d+\. )", raw)
    articles = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        pmid_m = re.search(r"PMID:\s*(\d{7,9})", block)
        if not pmid_m:
            continue
        pmid = pmid_m.group(1).strip()

        paragraphs = [p.strip() for p in re.split(r"\n[ \t]*\n", block) if p.strip()]

        # Year
        year = ""
        year_m = re.search(r"\b(19\d{2}|20[0-2]\d)\b", paragraphs[0] if paragraphs else "")
        if year_m:
            year = year_m.group(1)

        # Title — paragraph 1, collapsed
        title = ""
        if len(paragraphs) > 1:
            raw_t = re.sub(
                r"\n?(DOI|PMID|PMCID|Copyright|Conflict|Author information).*$",
                "", paragraphs[1], flags=re.DOTALL | re.IGNORECASE
            ).strip()
            title = " ".join(raw_t.split())
        if not title:
            title = f"Research Article (PMID {pmid})"

        # Authors — paragraph 2, strip affiliation markers
        authors = ""
        if len(paragraphs) > 2:
            raw_a = paragraphs[2]
            if not raw_a.lower().startswith("author information"):
                cleaned = re.sub(r"\(\d+\)", "", raw_a)
                cleaned = " ".join(cleaned.split()).strip(";. ")
                parts   = [p.strip() for p in cleaned.split(",") if p.strip()]
                parts   = [re.sub(r"\s+[A-Z]{1,3}$", "", p).strip() for p in parts if p]
                if len(parts) > 3:
                    authors = f"{parts[0]}, {parts[1]} et al."
                elif parts:
                    authors = ", ".join(parts)

        articles.append({
            "pmid": pmid, "title": title,
            "authors": authors, "year": year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    return articles


# ── TASK 3 — Cache-first PubMed search per factor ────────────────────────────
def _search_per_factor(elevated_factors: list[str],
                        status_fn) -> dict[str, list[dict]]:
    """
    For each of the top 3 elevated factors:
      1. Check ChromaDB cache first (semantic similarity)
      2. If cache miss → call PubMed MCP
      3. Store new results in cache
    Returns {factor_name: [article, ...]}
    """
    results = {}
    for factor in elevated_factors[:3]:
        query    = _query_for_factor(factor)
        # --- Cache lookup ---
        cached = _cache_lookup(query)
        if cached:
            status_fn(f"[Cache] *Found cached article(s) for \"{factor}\"*")
            results[factor] = cached
            continue
        # --- PubMed search ---
        status_fn(f"[PubMed] *Searching for \"{factor}\": {query[:55]}...*")
        raw      = search_pubmed_sync(query, max_results=2)
        articles = _parse_pubmed_articles(raw)
        if articles:
            _cache_store(query, articles)   # persist for future queries
            results[factor] = articles

    return results


def _all_articles(factor_articles: dict[str, list[dict]]) -> list[dict]:
    seen, out = set(), []
    for arts in factor_articles.values():
        for a in arts:
            if a["pmid"] not in seen:
                seen.add(a["pmid"])
                out.append(a)
    return out


# ── TASK 2 — Format: one citation per factor, inline ─────────────────────────
def _format_pubmed_for_llm(factor_articles: dict[str, list[dict]]) -> str:
    """
    Give the LLM exactly ONE ready-made Markdown citation per factor.
    No [Ref N] labels. Model must copy the citation verbatim.
    """
    if not factor_articles:
        return "NO_PUBMED_RESULTS"

    lines = [
        "VERIFIED CITATIONS — copy the CITATION TO USE line verbatim.",
        "One citation per factor. DO NOT invent others.\n",
    ]
    for factor, arts in factor_articles.items():
        a = arts[0]   # best match (first result)
        cite = (
            f"[{a['authors'] or 'Authors'}, {a['year']} — "
            f"{a['title']}]({a['url']})"
        )
        lines.append(
            f"FACTOR: {factor}\n"
            f"  CITATION TO USE: {cite}"
        )
        lines.append("")
    return "\n".join(lines)


# ── Hard sanitiser ────────────────────────────────────────────────────────────
def _sanitise_citations(answer: str, real_articles: list[dict],
                         factor_articles: dict | None = None) -> str:
    """
    - Strip any PubMed link whose PMID is not in real_articles.
    - In the Sources section, show ONLY articles that are linked
      to the top elevated factors (factor_articles), not every
      cached article ever retrieved.
    """
    # Build set of PMIDs that were actually fetched for THIS query's factors
    used_pmids = {a["pmid"] for a in real_articles}

    def _chk_md(m):
        p = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", m.group(0))
        return "" if (p and p.group(1) not in used_pmids) else m.group(0)

    def _chk_bare(m):
        p = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", m.group(0))
        return "" if (p and p.group(1) not in used_pmids) else m.group(0)

    answer = re.sub(r"\[([^\]]*)\]\(https?://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?\)", _chk_md, answer)
    answer = re.sub(r"https?://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?", _chk_bare, answer)
    answer = re.sub(r"Verified URL:\s*https?://\S+", "", answer)
    answer = re.sub(r"\[Ref\s*\d+\]", "", answer)
    answer = re.sub(r"- Evidence:.*?\[Ref\s*\d+\].*\n?", "", answer)
    answer = re.sub(r"- Evidence:.*?[Nn]o (specific |direct )?.*?available.*\n?", "", answer)
    answer = re.sub(r"\[\d{1,2}\](?!\()", "", answer)
    answer = re.sub(r"\s*\(\d{1,2}\)(?!\s*\w)", "", answer)
    answer = re.sub(r"\[\]\([^\)]*\)", "", answer)
    answer = re.sub(r"\n+References:.*$", "", answer, flags=re.DOTALL | re.IGNORECASE)
    answer = re.sub(r"  +", " ", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()

    # Build sources — one article per factor, only the best match per factor
    # This prevents all cached articles from flooding the sources section
    if factor_articles:
        shown = []
        seen_pmids = set()
        for factor, arts in factor_articles.items():
            for a in arts[:1]:   # only best match per factor
                if a["pmid"] not in seen_pmids and a["pmid"] in used_pmids:
                    seen_pmids.add(a["pmid"])
                    shown.append((factor, a))
        if shown:
            src = "\n\n---\n**Sources — Verified PubMed Articles (matched to your county's risk factors):**\n"
            for factor, a in shown:
                label = (f"{a['authors']}, {a['year']}" if a["authors"] and a["year"]
                         else a["year"] or "Article")
                src  += f"- **{factor}:** [{label} — {a['title']}]({a['url']})\n"
            answer += src
    elif real_articles:
        src = "\n\n---\n**Sources — Verified PubMed Articles:**\n"
        for i, a in enumerate(real_articles, 1):
            label = (f"{a['authors']}, {a['year']}" if a["authors"] and a["year"]
                     else a["year"] or f"Article {i}")
            src  += f"{i}. [{label} — {a['title']}]({a['url']})\n"
        answer += src

    return answer


# ── System prompt ─────────────────────────────────────────────────────────────
def _build_system_prompt(county_context: str, intent: str,
                          elevated_factors: list[str],
                          pubmed_block: str,
                          reply_language: str = "English") -> str:

    has_pubmed = pubmed_block and pubmed_block != "NO_PUBMED_RESULTS"

    # TASK 4 — language instruction
    lang_rule = (
        f"LANGUAGE RULE: The user wrote in {reply_language}. "
        f"You MUST reply entirely in {reply_language}. "
        f"All headings, bullet points, and sentences must be in {reply_language}.\n"
        if reply_language != "English" else ""
    )

    citation_rule = (
        "CITATION RULE — ABSOLUTE:\n"
        "  The VERIFIED CITATIONS block below gives you ready-made Markdown links.\n"
        "  Copy the 'CITATION TO USE' text EXACTLY into the Evidence line for that factor.\n"
        "  DO NOT write [Ref N], [1], (1), or any numbered reference.\n"
        "  DO NOT invent journal names or study descriptions.\n"
        "  DO NOT write 'A study published in...' or 'A review of N studies...'.\n"
        "  If no citation is provided for a factor, OMIT the Evidence line entirely.\n"
        if has_pubmed else
        "CITATION RULE — ABSOLUTE:\n"
        "  No PubMed results available for this query.\n"
        "  DO NOT include any Evidence lines, links, [Ref N], or study descriptions.\n"
    )

    pubmed_section = f"\n{pubmed_block}\n" if has_pubmed else ""

    prompt = (
        f"{lang_rule}"
        "You are a public health specialist analysing Social Determinants of Health (SDoH).\n\n"
        f"COUNTY DATA:\n{county_context}\n"
        f"{pubmed_section}\n"
        "STRICT RULES:\n"
        "1. Use ACTUAL NUMBERS from the county data (e.g. '27.08% vs US avg 15.1%').\n"
        "2. Address ONLY factors elevated above the US average.\n"
        "   NEVER list Internet Subscription Rate or Grocery Store Density as risks.\n"
        "3. Keep answers SHORT and scannable. No paragraph explanations per factor.\n"
        "4. Plain language. Explain medical terms in one phrase.\n"
        f"{citation_rule}"
    )

    if intent == "risk":
        prompt += """
TASK: Risk factor summary.

FORMAT — follow EXACTLY:

**{County} — Risk Snapshot**
| Factor | County | US Avg | Gap |
|---|---|---|---|
(top 6 elevated factors, largest gap first — exclude Internet Subscription Rate and Grocery Store Density)

**Top 3 Priorities**
1. [Factor] — [value] vs [US avg] — [max 10-word reason]
2. [Factor] — [value] vs [US avg] — [max 10-word reason]
3. [Factor] — [value] vs [US avg] — [max 10-word reason]

**Bottom line:** [One sentence.]

NO extra sections. NO paragraphs. NO bullet explanations.
"""
    elif intent == "care":
        prompt += """
TASK: Evidence-based interventions for the TOP 3 most elevated factors.

FORMAT — follow EXACTLY:

**Interventions for {County}**

**1. [Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words, specific to this county]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**2. [Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**3. [Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**Quick Wins**
- [one line]
- [one line]
- [one line]

NO [Ref N] labels. NO invented citations. NO extra sections.
"""
    else:  # mixed
        prompt += """
TASK: Crisp risk table + top 3 interventions.

FORMAT — follow EXACTLY:

**{County} — Risks & Actions**

| Factor | County | US Avg | Gap |
|---|---|---|---|
(top 5 elevated factors, largest gap first — exclude protective factors)

**Evidence-Based Interventions**

**1. [Top Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**2. [Second Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**3. [Third Factor] — [county value] vs [US avg]**
- Intervention: [specific program name]
- How: [one sentence, ≤15 words]
- Evidence: [paste CITATION TO USE here, or omit line if none]

**Quick Wins**
- [one line]
- [one line]
- [one line]

NO [Ref N] labels. NO invented citations. NO extra sections.
"""
    return prompt


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def ask_bot(user_question: str, county_context: str,
            chat_history: list, status_callback=None) -> tuple[str, list]:

    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    # TASK 4 — detect language
    reply_lang = _detect_language(user_question)
    if reply_lang != "English":
        _status(f"*Language detected: {reply_lang} — will reply in {reply_lang}*")

    intent = classify_intent(user_question)

    # ── Direct FIPS lookup — answer immediately, no LLM needed ───────────────
    if intent == "fips_lookup":
        _status("*Looking up FIPS code from county data...*")
        answer = _lookup_fips(county_context)
        updated_history = list(chat_history) + [
            {"role": "user",      "content": user_question},
            {"role": "assistant", "content": answer},
        ]
        return answer, updated_history, int((len(user_question.split()) + len(answer.split())) * 1.3) + 10

    # ── Greeting / farewell / casual ─────────────────────────────────────────
    if intent == "greeting":
        _status("*Greeting detected...*")
        # Extract county name for a friendly context-aware reply
        name_m = re.search(r"County:\s*(.+?),", county_context)
        county_name = name_m.group(1).strip() if name_m else "your county"
        ql = user_question.strip().lower()
        if re.search(r"\b(bye|goodbye|see you|cya|later|tata)\b", ql):
            answer = f"Goodbye! Come back anytime to explore health data for {county_name}. Take care!"
        elif re.search(r"\b(thanks|thank you|thx|ty)\b", ql):
            answer = f"You're welcome! Let me know if you have more questions about {county_name}."
        elif re.search(r"\b(how are you|how r u)\b", ql):
            answer = f"I'm doing well, thanks! Ready to help you explore health data for {county_name}. What would you like to know?"
        else:
            answer = f"Hello! I'm your SDoH health assistant for {county_name}. Ask me about risk factors, interventions, or the FIPS code."
        updated_history = list(chat_history) + [
            {"role": "user",      "content": user_question},
            {"role": "assistant", "content": answer},
        ]
        return answer, updated_history, int((len(user_question.split()) + len(answer.split())) * 1.3) + 10

    # ── "My county / my place" — return county summary ───────────────────────
    if intent == "county_info":
        _status("*Fetching county info...*")
        answer = _county_summary(county_context)
        updated_history = list(chat_history) + [
            {"role": "user",      "content": user_question},
            {"role": "assistant", "content": answer},
        ]
        return answer, updated_history, int((len(user_question.split()) + len(answer.split())) * 1.3) + 10

    _status(f"*Intent: {'Risk Factor Analysis' if intent=='risk' else 'Care & Interventions' if intent=='care' else 'Full Analysis'}*")

    # TASK 1 — elevated factors excluding protective ones
    elevated = _extract_elevated_factors(county_context)
    _status(f"*Top elevated factors: {', '.join(elevated[:3])}{'...' if len(elevated)>3 else ''}*")

    # TASK 2 + 3 — cache-first PubMed per factor
    factor_articles: dict[str, list[dict]] = {}
    real_articles:   list[dict]            = []

    if intent in ("care", "mixed") and elevated:
        _status("*Checking citation cache and PubMed...*")
        factor_articles = _search_per_factor(elevated, _status)
        real_articles   = _all_articles(factor_articles)
        if real_articles:
            _status(f"*Found {len(real_articles)} verified article(s).*")
        else:
            _status("*No matching articles found — answering without citations.*")

    pubmed_block  = _format_pubmed_for_llm(factor_articles)
    system_prompt = _build_system_prompt(
        county_context, intent, elevated, pubmed_block, reply_lang
    )

    messages = [{"role": "system", "content": system_prompt}]
    trimmed  = [m for m in chat_history if m.get("role") in ("user","assistant")][-6:]
    messages.extend(trimmed)
    messages.append({"role": "user", "content": user_question})

    client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    _status("*Writing answer...*")

    try:
        resp = client.chat.completions.create(
            model=PRIMARY_MODEL, messages=messages,
            temperature=0.1, max_tokens=900,
        )
    except Exception:
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL, messages=messages,
            temperature=0.1, max_tokens=900,
        )

    answer = (resp.choices[0].message.content or "").strip()
    if not answer:
        answer = "Unable to generate a response. Please rephrase your question."

    answer = _sanitise_citations(answer, real_articles, factor_articles)

    tokens_used = 0
    if resp and hasattr(resp, "usage") and resp.usage:
        tokens_used = getattr(resp.usage, "total_tokens", 0) or (len(user_question.split()) + len(answer.split()))
    else:
        # Fallback token estimation (approx 1.3 tokens per word)
        tokens_used = int((len(user_question.split()) + len(answer.split())) * 1.3) + 15

    updated_history = list(chat_history) + [
        {"role": "user",      "content": user_question},
        {"role": "assistant", "content": answer},
    ]
    return answer, updated_history, tokens_used


# ══════════════════════════════════════════════════════════════════════════════
# Context builder
# ══════════════════════════════════════════════════════════════════════════════

def build_county_context(c_name, c_state, c_pop, c_income, c_svi,
                          sdoh_df, health_df) -> str:
    import pandas as pd

    ctx  = f"County: {c_name}, {c_state}\n"
    ctx += f"Population: {int(c_pop):,}\n"

    if c_income and not (isinstance(c_income, float) and pd.isna(c_income)):
        ctx += f"Median Household Income: ${float(c_income):,.0f}\n"

    if c_svi and not (isinstance(c_svi, float) and pd.isna(c_svi)):
        svi_val = float(c_svi)
        label = (
            "(Very High Vulnerability)" if svi_val >= 0.75 else
            "(High Vulnerability)"      if svi_val >= 0.50 else
            "(Moderate Vulnerability)"  if svi_val >= 0.30 else
            "(Low Vulnerability)"
        )
        ctx += f"SVI Score: {svi_val:.4f}  {label}\n"

    ctx += "\nSDoH Factors — County vs US Average:\n"
    if sdoh_df is not None and not sdoh_df.empty:
        for _, row in sdoh_df.head(12).iterrows():
            factor = row.get("SDoH Barrier Factor", "Factor")
            val    = row.get("County Value", 0)
            unit   = row.get("Unit", "")
            us_avg = row.get("US National Average", 0)
            try:
                diff = float(val) - float(us_avg)
                # TASK 1: protective factors — label them as protective, not risk
                is_protective = factor.lower() in _PROTECTIVE_FACTORS
                if is_protective:
                    flag = f" [Protective — above avg by {diff:.1f}{unit}]" if diff > 0 else f" [below avg by {abs(diff):.1f}{unit}]"
                else:
                    flag = f" [ABOVE avg by {diff:.1f}{unit}]" if diff > 0 else f" [below avg by {abs(diff):.1f}{unit}]"
            except Exception:
                flag = ""
            ctx += f"  - {factor}: {val}{unit}  (US avg: {us_avg}{unit}){flag}\n"

    ctx += "\nHealth Outcomes — County vs US Average:\n"
    if health_df is not None and not health_df.empty:
        for _, row in health_df.iterrows():
            condition = row.get("Health Condition", "Condition")
            val       = row.get("County Prevalence (%)", 0)
            us_avg    = row.get("US National Avg (%)", 0)
            try:
                diff = float(val) - float(us_avg)
                flag = f" [ABOVE avg by {diff:.1f}%]" if diff > 0 else f" [below avg by {abs(diff):.1f}%]"
            except Exception:
                flag = ""
            ctx += f"  - {condition}: {val}%  (US avg: {us_avg}%){flag}\n"

    return ctx
