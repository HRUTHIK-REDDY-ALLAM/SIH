"""LangGraph orchestration of the underwriting pipeline.

The graph is: data_gathering → invoice_verification → fraud_check →
buyer_verification → risk_scoring → compliance_kyc → finalize, with
conditional halt edges out of the first three nodes (missing consent, invalid
invoice, duplicate financing) that jump straight to finalize.
"""
import threading
import traceback
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..audit import Recorder
from ..db import SessionLocal, now_utc
from ..models import FinancingDeal
from ..serialize import inr
from . import nodes


class UWState(TypedDict, total=False):
    halted: bool
    halt_reason: str


def _route(state: UWState) -> str:
    return "halt" if state.get("halted") else "continue"


def build_graph(ctx: nodes.PipelineContext):
    g = StateGraph(UWState)
    g.add_node("data_gathering", nodes.data_gathering(ctx))
    g.add_node("invoice_verification", nodes.invoice_verification(ctx))
    g.add_node("fraud_check", nodes.fraud_check(ctx))
    g.add_node("buyer_verification", nodes.buyer_verification(ctx))
    g.add_node("risk_scoring", nodes.risk_scoring(ctx))
    g.add_node("compliance_kyc", nodes.compliance_kyc(ctx))
    g.add_node("finalize", nodes.finalize(ctx))

    g.add_edge(START, "data_gathering")
    g.add_conditional_edges("data_gathering", _route,
                            {"halt": "finalize", "continue": "invoice_verification"})
    g.add_conditional_edges("invoice_verification", _route,
                            {"halt": "finalize", "continue": "fraud_check"})
    g.add_conditional_edges("fraud_check", _route,
                            {"halt": "finalize", "continue": "buyer_verification"})
    g.add_edge("buyer_verification", "risk_scoring")
    g.add_edge("risk_scoring", "compliance_kyc")
    g.add_edge("compliance_kyc", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


def run_pipeline(deal_id: int) -> None:
    db = SessionLocal()
    try:
        deal = db.get(FinancingDeal, deal_id)
        if deal is None:
            return
        invoice = deal.invoice
        ctx = nodes.PipelineContext(
            db=db, rec=Recorder(db, deal_id), deal=deal,
            invoice=invoice, msme=deal.msme, buyer=invoice.buyer,
        )
        ctx.rec.sys(f"Agent session started · LangGraph pipeline over {invoice.code} "
                    f"for {inr(invoice.amount)} to {invoice.buyer.name}")
        graph = build_graph(ctx)
        graph.invoke({"halted": False})
    except Exception:
        db.rollback()
        deal = db.get(FinancingDeal, deal_id)
        if deal is not None:
            deal.status = "error"
            deal.error = traceback.format_exc(limit=5)
            deal.decided_at = now_utc()
            db.commit()
            try:
                Recorder(db, deal_id).sys("Pipeline error — the run was stopped safely. See deal.error.")
            except Exception:
                pass
    finally:
        db.close()


def start_pipeline(deal_id: int) -> None:
    threading.Thread(target=run_pipeline, args=(deal_id,), daemon=True).start()
