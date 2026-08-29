/** Student-facing search labels — keep in sync with backend status_copy.py */

export function statusLabelsFor(query: string): string[] {
  const q = query.trim().toLowerCase();
  let first = "Searching campus guidelines…";
  if (/refund|वापसी|withdraw|cancellation/.test(q)) first = "Reading refund rules…";
  else if (/fee|fees|शुल्क|tuition|mess/.test(q)) first = "Looking through fee circulars…";
  else if (/attend|उपस्थिति|dugc|shortfall/.test(q)) first = "Checking attendance guidelines…";
  else if (/hostel|हॉस्टल|हॉस्टेल|warden/.test(q)) first = "Opening hostel notices…";
  else if (/\b(20\d{2})\b|क्या था/.test(q)) first = "Matching the year you asked about…";
  else if (/[\u0900-\u097F]/.test(query)) first = "Reading Hindi and English circulars…";

  return [
    first,
    "Finding the closest official passages…",
    "Checking whether two documents disagree…",
    "Writing an answer with citations…",
  ];
}
