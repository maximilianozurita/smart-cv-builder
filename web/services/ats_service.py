"""ATS keyword scoring — no external NLP dependencies."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# ~150 common English stopwords
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "dare", "ought", "used", "able",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "them", "their", "this", "that", "these", "those", "what", "which", "who",
    "whom", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "just", "don",
    "now", "ll", "m", "o", "re", "ve", "y", "ain", "aren", "couldn", "didn",
    "doesn", "hadn", "hasn", "haven", "isn", "ma", "mightn", "mustn",
    "needn", "shan", "shouldn", "wasn", "weren", "won", "wouldn",
    "as", "its", "also", "any", "while", "after", "before", "since",
    "between", "within", "without", "across", "against", "along", "among",
    "around", "behind", "below", "beside", "beyond", "except", "following",
    "including", "near", "over", "per", "plus", "regarding", "throughout",
    "under", "unlike", "until", "upon", "versus", "via", "whether", "yet",
    "team", "work", "working", "years", "year", "experience", "role", "job",
    "position", "company", "candidate", "strong", "good", "great", "excellent",
    "required", "preferred", "must", "ability", "skills", "knowledge",
    "new", "use", "using", "one", "two", "three", "well", "provide", "make",
    "ensure", "help", "support", "manage", "including", "related", "various",
}


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if w and w not in _STOPWORDS and len(w) > 2]


def _normalize(word: str) -> str:
    """
    Stem a word by removing common suffixes.
    Longer/more-specific suffixes are checked first.
    's' before 'es' so 'microservices' → 'microservice' (not 'microservic').
    'ation' before 'tion' so 'optimization' → 'optimiz' (not 'optimiza').
    """
    for suffix in ("ations", "ation", "tions", "tion", "ings", "ing", "ers", "er", "ed", "s", "es"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: len(word) - len(suffix)]
    return word


def _extract_terms(text: str) -> List[str]:
    """Return normalized unigrams + original bigrams for a text."""
    tokens = _tokenize(text)
    normalized = [_normalize(t) for t in tokens]
    bigrams = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
    return normalized + bigrams


def _weighted_terms(text: str) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Build a {normalized_term: weight} dict from the JD, plus a
    {normalized_term: display_label} dict with the original word for UI display.

    Splits at token boundary (not char boundary) — no mid-word fragments.
    Terms in the first 20% of tokens get 1.5× weight.
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}, {}

    cutoff_idx = max(1, int(len(tokens) * 0.20))

    weights: Dict[str, float] = {}
    display: Dict[str, str] = {}  # normalized → best original form (shortest = most readable)

    for i, token in enumerate(tokens):
        norm = _normalize(token)
        w = 1.5 if i < cutoff_idx else 1.0
        weights[norm] = weights.get(norm, 0) + w
        # Prefer the shortest original form as display label (e.g. "design" over "designing")
        if norm not in display or len(token) < len(display[norm]):
            display[norm] = token

    # Bigrams (original tokens, no normalization — they're already clean)
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i + 1]}"
        w = 1.5 if i < cutoff_idx else 1.0
        weights[bigram] = weights.get(bigram, 0) + w
        display[bigram] = bigram  # bigrams display as-is

    return weights, display


def _match_score(
    cv_text: str,
    jd_terms: Dict[str, float],
) -> Tuple[float, List[str], List[str]]:
    cv_terms = set(_extract_terms(cv_text))
    matched = []
    missing = []
    matched_weight = 0.0
    total_weight = sum(jd_terms.values())

    for term, w in jd_terms.items():
        if term in cv_terms:
            matched.append(term)
            matched_weight += w
        else:
            missing.append(term)

    score = (matched_weight / total_weight * 100) if total_weight > 0 else 0.0
    missing.sort(key=lambda t: jd_terms.get(t, 0), reverse=True)
    return score, matched, missing


def score_ats(
    job_description: str,
    profile: str,
    skills: str,
    experience_bullets: List[str],
) -> dict:
    """
    Returns: {score, matched_keywords, missing_keywords, section_scores}
    score is 0-100. Keywords use original display forms, not stems.
    """
    jd_terms, display = _weighted_terms(job_description)
    if not jd_terms:
        return {
            "score": 0.0,
            "matched_keywords": [],
            "missing_keywords": [],
            "section_scores": {},
        }

    exp_text = " ".join(experience_bullets)
    p_score, p_matched, _ = _match_score(profile, jd_terms)
    s_score, s_matched, _ = _match_score(skills, jd_terms)
    e_score, e_matched, _ = _match_score(exp_text, jd_terms)

    all_matched_keys = list(dict.fromkeys(p_matched + s_matched + e_matched))

    # Missing = top-weight JD terms absent across all CV sections
    cv_all = " ".join([profile, skills, exp_text])
    _, _, missing_keys = _match_score(cv_all, jd_terms)
    # Filter out bigrams from missing display (unigrams are more actionable)
    missing_keys = [t for t in missing_keys if " " not in t][:20]

    global_score = p_score * 0.25 + s_score * 0.40 + e_score * 0.35

    # Translate stems → display labels
    def _labels(keys: List[str]) -> List[str]:
        return [display.get(k, k) for k in keys]

    return {
        "score": round(global_score, 1),
        "matched_keywords": _labels(all_matched_keys)[:30],
        "missing_keywords": _labels(missing_keys),
        "section_scores": {
            "profile": round(p_score, 1),
            "skills": round(s_score, 1),
            "experience": round(e_score, 1),
        },
    }
