"""Student-facing search status lines — query-aware, then staged."""

from __future__ import annotations

import re

_FEE = re.compile(r"fee|fees|शुल्क|tuition|hostel fee|mess", re.I)
_HOSTEL = re.compile(r"hostel|हॉस्टल|हॉस्टेल|warden", re.I)
_ATTEND = re.compile(r"attend|उपस्थिति|dugc|shortfall", re.I)
_REFUND = re.compile(r"refund|वापसी|withdraw|cancellation", re.I)
_YEAR = re.compile(r"\b(20\d{2})\b|क्या था|in 20", re.I)


def labels_for(query: str) -> list[str]:
    q = (query or "").strip()
    if _REFUND.search(q):
        first = "Reading refund rules…"
    elif _FEE.search(q):
        first = "Looking through fee circulars…"
    elif _ATTEND.search(q):
        first = "Checking attendance guidelines…"
    elif _HOSTEL.search(q):
        first = "Opening hostel notices…"
    elif _YEAR.search(q):
        first = "Matching the year you asked about…"
    elif any("\u0900" <= ch <= "\u097F" for ch in q):
        first = "Reading Hindi and English circulars…"
    else:
        first = "Searching campus guidelines…"

    return [
        first,
        "Finding the closest official passages…",
        "Checking whether two documents disagree…",
        "Writing an answer with citations…",
    ]
