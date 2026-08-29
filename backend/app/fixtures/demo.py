"""Mock answers that match the 4-minute demo script. Same event shape as live SSE."""

from __future__ import annotations

from typing import Any

DEMO: dict[str, list[dict[str, Any]]] = {
    "attendance": [
        {"type": "status", "label": "Searching academic guidelines…"},
        {
            "type": "sources",
            "items": [
                {
                    "n": 1,
                    "title": "Academic Guidelines UG (modified Dec 2025)",
                    "url": "https://www.iiitdmj.ac.in/academics/download/Annexure%20II%20_%20Academic%20Guidelines_UG%20modified%20Dec%202025.pdf",
                    "page": 12,
                    "excerpt": "A student must maintain the prescribed attendance to be eligible for end-semester examinations. Shortfall is dealt with by the DUGC.",
                    "effective_from": "2025-12-01",
                    "last_updated": "2025-12-01",
                },
                {
                    "n": 2,
                    "title": "Academic Guidelines UG and PG (2017)",
                    "url": "https://www.iiitdmj.ac.in/academics/download/Academic%20Guidelines_271017.pdf",
                    "page": 8,
                    "excerpt": "Earlier guidelines remain published. The 2025 manual states it supersedes prior sets after BoG approval.",
                    "effective_from": "2017-10-27",
                    "last_updated": "2017-10-27",
                },
            ],
        },
        {
            "type": "freshness",
            "asOf": "2025-12-01",
            "lastUpdated": "2025-12-01",
        },
        {
            "type": "token",
            "text": "For current UG students, attendance and exam eligibility are governed by the **December 2025 Academic Guidelines** [1], which the institute says supersede earlier manuals.\n\nYou need the attendance prescribed in that manual to sit end-semester exams. Shortfall goes to the Discipline Undergraduate Committee (DUGC). The 2017 guidelines [2] are still on the site — treat them as historical unless you were admitted under that cohort.",
        },
        {
            "type": "contradiction",
            "claim": "Which academic rules bind current UG students",
            "a": {
                "n": 1,
                "title": "UG Guidelines Dec 2025",
                "url": "https://www.iiitdmj.ac.in/academics/download/Annexure%20II%20_%20Academic%20Guidelines_UG%20modified%20Dec%202025.pdf",
                "page": 1,
                "excerpt": "These rules supersede all earlier sets after BoG approval.",
                "effective_from": "2025-12-01",
            },
            "b": {
                "n": 2,
                "title": "UG/PG Guidelines 2017",
                "url": "https://www.iiitdmj.ac.in/academics/download/Academic%20Guidelines_271017.pdf",
                "page": 1,
                "excerpt": "Still published on iiitdmj.ac.in as a current download.",
                "effective_from": "2017-10-27",
            },
        },
        {"type": "done"},
    ],
    "refund": [
        {"type": "status", "label": "Reading refund notification and FAQ…"},
        {
            "type": "sources",
            "items": [
                {
                    "n": 1,
                    "title": "Notification — Revised refund rule",
                    "url": "https://www.iiitdmj.ac.in/downloads/Notification_Revised_refund_rule.pdf",
                    "page": 1,
                    "excerpt": "For CSAB/CCMT/QIP/DASA/UCEED admissions, processing fee of ₹1000 is deducted. Later cancellations follow a 50% slab.",
                    "effective_from": "2023-05-15",
                    "last_updated": "2023-05-15",
                },
                {
                    "n": 2,
                    "title": "FAQ 2025",
                    "url": "https://www.iiitdmj.ac.in/downloads/FAQ%202025.pdf",
                    "page": 2,
                    "excerpt": "Fee refund rules are available here. For withdrawal before the last round contact JoSAA/CSAB authorities.",
                    "effective_from": "2025-01-01",
                    "last_updated": "2025-01-01",
                },
            ],
        },
        {
            "type": "structure",
            "kind": "fee",
            "title": "Institute refund notification (2023)",
            "rows": [
                {"when": "CSAB / CCMT / DASA / UCEED path", "kept": "₹1,000 processing", "returned": "Balance per notification"},
                {"when": "After a stated cutoff", "kept": "50% of paid fee", "returned": "Remaining 50%"},
            ],
        },
        {
            "type": "token",
            "text": "Two documents disagree on *who* processes a withdrawal refund.\n\nThe **2023 institute notification** [1] lists rupee slabs (₹1,000 processing on the counselling path, then a 50% slab). The **2025 FAQ** [2] tells you to contact **JoSAA/CSAB** for refunds before the last round.\n\nSuchna will not pick a winner. Both sources are below.",
        },
        {
            "type": "contradiction",
            "claim": "Fee refund on withdrawal",
            "a": {
                "n": 1,
                "title": "Revised refund rule (2023)",
                "url": "https://www.iiitdmj.ac.in/downloads/Notification_Revised_refund_rule.pdf",
                "page": 1,
                "excerpt": "Institute-side slabs including ₹1000 processing and 50% cancellation.",
                "effective_from": "2023-05-15",
            },
            "b": {
                "n": 2,
                "title": "FAQ 2025",
                "url": "https://www.iiitdmj.ac.in/downloads/FAQ%202025.pdf",
                "page": 2,
                "excerpt": "For refund of fees for withdrawal before the last round contact JoSAA/CSAB authorities.",
                "effective_from": "2025-01-01",
            },
        },
        {"type": "done"},
    ],
    "fee": [
        {"type": "status", "label": "Extracting fee tables…"},
        {
            "type": "sources",
            "items": [
                {
                    "n": 1,
                    "title": "Fee structure B.Tech / B.Des 2024-25",
                    "url": "https://www.iiitdmj.ac.in/academics/download/fee-structure-2024-25/UG2024.pdf",
                    "page": 1,
                    "excerpt": "Hostel fees ₹11,000 per semester including fan/electricity and hall establishment. Tuition ₹71,750 (Gen/OBC/EWS).",
                    "effective_from": "2024-07-01",
                    "last_updated": "2024-07-01",
                }
            ],
        },
        {
            "type": "freshness",
            "asOf": "2024-07-01",
            "lastUpdated": "2024-07-01",
        },
        {
            "type": "structure",
            "kind": "table",
            "title": "UG 2024 batch — per semester (₹)",
            "rows": [
                {"head": "Tuition (Gen/OBC/EWS)", "amount": "71,750"},
                {"head": "Tuition (PWD/SC/ST)", "amount": "NIL"},
                {"head": "Hostel (incl. electricity / hall)", "amount": "11,000"},
                {"head": "Academic semester fees (B)", "amount": "7,500"},
                {"head": "Mess advance (actuals)", "amount": "15,000"},
            ],
        },
        {
            "type": "token",
            "text": "For the **2024 B.Tech/B.Des batch**, hostel is **₹11,000 / semester** (fan, electricity, hall establishment; cooler extra) [1]. Gen/OBC/EWS tuition is **₹71,750**; SC/ST/PWD tuition is nil. Mess is a **₹15,000 advance**, adjusted to actuals.\n\nThis is the 2024–25 PDF. Confirm with Academic Office before paying — the sheet itself says fees are tentative.",
        },
        {"type": "done"},
    ],
    "hostel": [
        {"type": "status", "label": "Reading hostel page and fee tables…"},
        {
            "type": "sources",
            "items": [
                {
                    "n": 1,
                    "title": "Hostels @ IIITDM Jabalpur",
                    "url": "https://www.iiitdmj.ac.in/students/hostels.php",
                    "page": None,
                    "excerpt": "Fully residential. Halls: Vasishtha, Aryabhatta, Vivekananda, Panini, Maa Saraswati, Nagarjuna.",
                    "effective_from": "2023-08-24",
                    "last_updated": "2023-08-24",
                },
                {
                    "n": 2,
                    "title": "Fee structure UG 2024-25",
                    "url": "https://www.iiitdmj.ac.in/academics/download/fee-structure-2024-25/UG2024.pdf",
                    "page": 1,
                    "excerpt": "Hostel fees ₹11,000 per semester.",
                    "effective_from": "2024-07-01",
                },
            ],
        },
        {
            "type": "token",
            "text": "IIITDMJ is fully residential [1]. Current halls: **Vasishtha** (single), **Aryabhatta** and **Vivekananda** (triple), **Panini** (single/twin), **Maa Saraswati** (girls), **Nagarjuna** (PG married). Mess is run by wardens + a student committee.\n\nThe UG 2024 fee PDF lists hostel at **₹11,000 / semester** [2]. That line is a fee, not a hall allotment.",
        },
        {"type": "done"},
    ],
    "asof2023": [
        {"type": "status", "label": "Filtering documents by effective_from…"},
        {
            "type": "sources",
            "items": [
                {
                    "n": 1,
                    "title": "Academic Guidelines UG and PG (2017)",
                    "url": "https://www.iiitdmj.ac.in/academics/download/Academic%20Guidelines_271017.pdf",
                    "page": 6,
                    "excerpt": "The 2017 manual was the published UG/PG rulebook through 2023.",
                    "effective_from": "2017-10-27",
                    "last_updated": "2017-10-27",
                },
                {
                    "n": 2,
                    "title": "Academic Guidelines UG (modified Dec 2025)",
                    "url": "https://www.iiitdmj.ac.in/academics/download/Annexure%20II%20_%20Academic%20Guidelines_UG%20modified%20Dec%202025.pdf",
                    "page": 1,
                    "excerpt": "Current manual. Not in force in 2023.",
                    "effective_from": "2025-12-01",
                    "last_updated": "2025-12-01",
                },
            ],
        },
        {
            "type": "freshness",
            "asOf": "2023-12-31",
            "lastUpdated": "2017-10-27",
        },
        {
            "type": "token",
            "text": "**As of 2023**, the published UG/PG rulebook on the site is the **27 Oct 2017 Academic Guidelines** [1]. The December 2025 manual [2] did not exist yet — do not use it for a 2023 question.\n\nCurrent students should still check [2] for today's rule. This answer is dated on purpose.",
        },
        {"type": "done"},
    ],
}

CHIPS = {
    "attendance": ("What is the attendance policy?", "attendance"),
    "refund": ("वापसी का नियम क्या है?", "refund"),
    "fee": ("What is the hostel fee?", "fee"),
    "hostel": ("What does the hostel section say?", "hostel"),
    "asof2023": ("What was the rule in 2023?", "asof2023"),
}


def pick_demo(query: str) -> list[dict[str, Any]]:
    q = query.lower()
    if any(w in q for w in ("2023", "as of", "that year", "then")):
        return DEMO["asof2023"]
    if any(w in q for w in ("वापसी", "refund", "withdrawal", "नियम")):
        return DEMO["refund"]
    if any(w in q for w in ("attendance", "उपस्थिति", "dugc")):
        return DEMO["attendance"]
    if any(w in q for w in ("hostel fee", "tuition", "mess", "₹", "fee structure")):
        return DEMO["fee"]
    if any(w in q for w in ("hostel", "vasishtha", "hall")):
        return DEMO["hostel"]
    return DEMO["attendance"]
