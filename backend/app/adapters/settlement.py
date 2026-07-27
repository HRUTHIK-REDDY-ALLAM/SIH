# MOCK ADAPTER — no production credentials available (needs real banking rails).
# Production swap: partner-financier disbursement API over NEFT/RTGS and the
# UPI–PayNow corridor for the India↔Singapore leg. No real money moves here.
import secrets
from datetime import date


def disburse(*, deal_id: int, amount: int, account: str) -> dict:
    return {
        "utr": f"UTR N{date.today():%y%m%d}TB{deal_id:04d}{secrets.token_hex(2).upper()}",
        "rail": "NEFT · UPI–PayNow corridor (simulated)",
        "account": account,
        "amount": amount,
        "status": "success",
    }


def collect_repayment(*, deal_id: int, amount: int, payer: str) -> dict:
    return {
        "utr": f"UTR P{date.today():%y%m%d}TB{deal_id:04d}{secrets.token_hex(2).upper()}",
        "rail": "PayNow → escrow (simulated)",
        "payer": payer,
        "amount": amount,
        "status": "success",
    }
