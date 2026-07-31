"""Hash-anchored invoice fingerprinting.

The fingerprint is a SHA-256 over the invoice's *economic identity* — seller
GSTIN, buyer UEN, amount, issue date, currency — deliberately excluding the
invoice number and IRN. A fraudster who regenerates the e-invoice (new IRN),
renumbers it, or rewords the goods description produces the SAME fingerprint,
so the registry still recognises the receivable.

Production hardening (documented, not built): fuzzy anchors — amount rounded
to bands, ±3-day date windows, buyer-normalisation — each stored as an extra
anchor hash so near-miss edits also collide.
"""
import hashlib
from datetime import date


def invoice_fingerprint(*, gstin: str, buyer_uen: str, amount: int,
                        issued_on: date, currency: str = "INR") -> str:
    canonical = "|".join([
        gstin.strip().upper(),
        buyer_uen.strip().upper(),
        str(int(amount)),
        issued_on.isoformat(),
        currency.strip().upper(),
    ])
    return hashlib.sha256(canonical.encode()).hexdigest()


def short(fp: str) -> str:
    return f"{fp[:10]}…" if fp else "—"
