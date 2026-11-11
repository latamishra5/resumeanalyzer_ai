"""Pure filtering and suggestion helpers for job search."""

from typing import Dict, List


def filter_suggestions(query: str, suggestions: List[Dict]) -> List[Dict]:
    """Filter suggestions based on user input"""
    if not query:
        return []
    return [
        s for s in suggestions
        if query.lower() in s["text"].lower()
    ][:5]


def filter_location_suggestions(query: str, suggestions: List[Dict]) -> List[Dict]:
    """Filter location suggestions based on user input with smart categorization"""
    if not query or len(query) < 2:
        return []

    matching_states = [s for s in suggestions if s.get("type") == "state" and query.lower() in s["text"].lower()]
    matching_cities = [s for s in suggestions if s.get("type") == "city" and query.lower() in s["text"].lower()]
    matching_work_modes = [s for s in suggestions if s.get("type") == "work_mode" and query.lower() in s["text"].lower()]

    results = matching_states + matching_cities + matching_work_modes
    return results[:7]


def get_filter_options():
    """Get filter options for job search"""
    return {
        "experience_levels": [
            {"id": "all", "text": "All Levels"},
            {"id": "fresher", "text": "Fresher"},
            {"id": "0-1", "text": "0-1 years"},
            {"id": "1-3", "text": "1-3 years"},
            {"id": "3-5", "text": "3-5 years"},
            {"id": "5-7", "text": "5-7 years"},
            {"id": "7-10", "text": "7-10 years"},
            {"id": "10+", "text": "10+ years"},
        ],
        "salary_ranges": [
            {"id": "all", "text": "All Ranges"},
            {"id": "0-3", "text": "0-3 LPA"},
            {"id": "3-6", "text": "3-6 LPA"},
            {"id": "6-10", "text": "6-10 LPA"},
            {"id": "10-15", "text": "10-15 LPA"},
            {"id": "15+", "text": "15+ LPA"},
        ],
        "job_types": [
            {"id": "all", "text": "All Types"},
            {"id": "full-time", "text": "Full Time"},
            {"id": "part-time", "text": "Part Time"},
            {"id": "contract", "text": "Contract"},
            {"id": "remote", "text": "Remote"},
        ],
    }
