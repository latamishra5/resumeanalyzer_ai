"""Cloud-safe remote job feed client and resume-to-job skill match scorer."""

import logging
import re

import requests

logger = logging.getLogger(__name__)

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"

_KNOWN_TECH_KEYWORDS = (
    "python", "java", "javascript", "typescript", "c++", "go", "rust", "sql",
    "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws",
    "azure", "gcp", "terraform", "ci/cd", "git", "fastapi", "django", "flask",
    "react", "node.js", "next.js", "pandas", "numpy", "scikit-learn", "pytorch",
    "tensorflow", "tableau", "power bi", "spark", "airflow", "etl", "rest api",
    "graphql", "microservices", "agile", "scrum", "figma", "pytest", "linux",
    "llm", "rag", "gemini", "html", "css", "machine learning", "data analysis",
)


def _strip_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", str(raw_text))
    return re.sub(r"\s+", " ", cleaned).strip()


def _safe_http_url(raw_url: str | None) -> str:
    val = str(raw_url or "").strip()
    if val.startswith(("http://", "https://")):
        return val
    return ""


def normalize_skills_input(resume_skills) -> list[str]:
    """Normalize a list or comma-separated string of resume skills."""
    if not resume_skills:
        return []
    if isinstance(resume_skills, str):
        items = [part.strip() for part in resume_skills.split(",")]
    else:
        items = [str(part).strip() for part in resume_skills]

    deduped = []
    seen = set()
    for item in items:
        low = item.lower()
        if item and low not in seen:
            seen.add(low)
            deduped.append(item)
    return deduped


def compute_job_match_score(
    resume_skills,
    job_title: str = "",
    job_description: str = "",
    job_tags: list[str] | None = None,
) -> dict:
    """Compute a deterministic percentage match between candidate skills and a job listing."""
    candidate_skills = normalize_skills_input(resume_skills)
    candidate_map = {s.lower(): s for s in candidate_skills}

    job_corpus = f"{job_title or ''} {_strip_html(job_description)}".lower()
    target_terms = []
    seen_targets = set()

    for tag in job_tags or []:
        t = str(tag or "").strip()
        if t and t.lower() not in seen_targets:
            seen_targets.add(t.lower())
            target_terms.append(t)

    for kw in _KNOWN_TECH_KEYWORDS:
        if kw not in seen_targets and re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", job_corpus):
            seen_targets.add(kw)
            target_terms.append(kw.upper() if len(kw) <= 3 else kw.title())

    if not candidate_map:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": target_terms[:8],
        }

    if not target_terms:
        # Compare candidate skills directly against job text
        matched = [orig for low, orig in candidate_map.items() if low in job_corpus]
        score = min(100, round((len(matched) / max(len(candidate_map), 1)) * 100))
        return {
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": [],
        }

    matched = []
    missing = []
    for target in target_terms:
        t_low = target.lower()
        if any(t_low == c_low or t_low in c_low or c_low in t_low for c_low in candidate_map):
            matched.append(target)
        else:
            missing.append(target)

    score = round((len(matched) / len(target_terms)) * 100) if target_terms else 0
    return {
        "match_score": max(0, min(100, int(score))),
        "matched_skills": matched[:10],
        "missing_skills": missing[:8],
    }


def fetch_remote_jobs(query: str = "", limit: int = 12, timeout: int = 8) -> dict:
    """Fetch cloud-safe remote job listings from Remotive's public API."""
    search_term = str(query or "").strip()
    if not search_term:
        return {"jobs": [], "error": "Enter a job title or skill to search live remote roles."}

    try:
        response = requests.get(
            REMOTIVE_API_URL,
            params={"search": search_term, "limit": max(1, min(int(limit), 30))},
            headers={"User-Agent": "ResumeAnalyzerAI/1.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        jobs = []
        for item in raw_jobs[:limit]:
            if not isinstance(item, dict):
                continue
            desc = _strip_html(item.get("description", ""))
            jobs.append({
                "title": str(item.get("title") or "Untitled Role").strip(),
                "company": str(item.get("company_name") or "Unknown Company").strip(),
                "location": str(item.get("candidate_required_location") or "Remote").strip(),
                "job_type": str(item.get("job_type") or "Full-time").replace("_", " ").title(),
                "salary": str(item.get("salary") or "Not disclosed").strip(),
                "tags": [str(t).strip() for t in (item.get("tags") or []) if str(t).strip()][:8],
                "url": _safe_http_url(item.get("url")),
                "published_at": str(item.get("publication_date") or "")[:10],
                "summary": desc[:260] + ("..." if len(desc) > 260 else ""),
                "description": desc,
            })
        return {"jobs": jobs, "error": None}
    except requests.RequestException as exc:
        logger.warning("Remote job feed request failed: %s", exc)
        return {
            "jobs": [],
            "error": "Unable to reach the live remote job feed right now. Use Job Portal links or try again shortly.",
        }
    except Exception as exc:
        logger.warning("Unexpected error parsing remote job feed: %s", exc)
        return {
            "jobs": [],
            "error": "Could not parse remote job feed response.",
        }
