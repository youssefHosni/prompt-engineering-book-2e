---
name: invoice-validation
description: >
  Check a supplier invoice against the purchase order and the goods receipt
  before it is approved for payment. Use when asked to validate, check or
  reconcile an invoice. Do not use to create invoices, chase payment, or
  answer tax questions.
---

A three-way match, done in an order that fails fast.

## Steps

1. Extract the invoice number, supplier, date, currency and total.
2. Reject immediately if any of those five is missing.
3. Find the purchase order referenced on the invoice.
4. If no PO is referenced, stop and ask. Do not guess from the supplier.
5. Confirm the PO is open, not cancelled or already fully invoiced.
6. Confirm the supplier on the invoice matches the supplier on the PO exactly.
7. A near-match on supplier name is a mismatch. Do not normalise it away.
8. Find the goods receipt for the PO.
9. If no goods receipt exists, the invoice cannot be approved yet. Say so.
10. Compare invoice line count with PO line count.
11. For each invoice line, find the matching PO line by part number.
12. Match on part number only, never on description.
13. Flag any invoice line with no matching PO line.
14. Flag any PO line with no matching invoice line as a partial delivery.
15. For each matched line, compare unit price with the PO unit price.
16. A unit price above the PO price is a variance regardless of size.
17. A unit price below the PO price is also a variance. Report both.
18. For each matched line, compare quantity invoiced with quantity received.
19. Quantity invoiced above quantity received is the most common fraud shape.
20. Recompute every line total from unit price and quantity.
21. Recompute the invoice subtotal from the line totals.
22. Do not trust the subtotal printed on the invoice.
23. Check the tax rate against the supplier's registered rate.
24. Recompute the tax from the subtotal.
25. Recompute the grand total.
26. Compare your grand total with the printed total to the penny.
27. Any discrepancy, however small, is reported and not rounded away.
28. Check the currency matches the PO currency.
29. If currencies differ, stop. Do not apply an exchange rate.
30. Check the invoice date is not before the goods receipt date.
31. Check the invoice has not already been paid under another number.
32. Search for the same supplier, amount and date within 90 days.
33. Check payment terms on the invoice match the PO terms.
34. Compute the due date from the invoice date and the PO terms.
35. Summarise as: match, variance, or reject, with the reasons.
36. A variance under the tolerance in `references/tolerances.md` still gets listed.
37. STOP. Present the summary and ask before recording an outcome.
38. On approval, write the outcome to the invoice record.
39. Never mark an invoice approved. Approval is a human action.
40. Record every check performed, including the ones that passed.

## Rules

- Never approve. Recommend, and let a person approve.
- Never normalise a supplier name to make a match work.
- Never apply an exchange rate. A currency mismatch is an exception.
- Never round a discrepancy away, however small.
- If the PO cannot be found, stop. Do not infer it from the supplier.
- Report checks that passed as well as checks that failed.
- A duplicate-payment hit is escalated immediately, not listed with the rest.
