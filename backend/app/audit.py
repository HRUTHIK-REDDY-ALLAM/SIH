import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import PACING
from .models import AuditEvent


class Recorder:
    """Writes every pipeline event to the audit_log table, committing per event
    so the frontend's polling sees progress live. The per-line delay is what
    paces the demo; the rows are what make the explainability real."""

    def __init__(self, db: Session, deal_id: int):
        self.db = db
        self.deal_id = deal_id
        last = db.execute(
            select(func.max(AuditEvent.seq)).where(AuditEvent.deal_id == deal_id)
        ).scalar()
        self.seq = last or 0

    def _emit(self, event: str, *, node=None, status=None, kind=None, message=None, data=None):
        self.seq += 1
        self.db.add(AuditEvent(
            deal_id=self.deal_id, seq=self.seq, node=node, event=event,
            status=status, kind=kind, message=message, data=data,
        ))
        self.db.commit()

    def sys(self, text: str, data: dict | None = None):
        self._emit("sys", kind="sys", message=text, data=data)

    def node_start(self, node: str):
        self._emit("node_start", node=node, status="running")

    def line(self, node: str, kind: str, text: str, delay: float = 0.4, data: dict | None = None):
        if delay and PACING:
            time.sleep(delay * PACING)
        self._emit("line", node=node, kind=kind, message=text, data=data)

    def node_complete(self, node: str, status: str, finding: str | None):
        if PACING:
            time.sleep(0.3 * PACING)
        self._emit("node_complete", node=node, status=status, message=finding)

    def decision(self, payload: dict):
        self._emit("decision", message=payload.get("headline"), data=payload)

    def settlement(self, text: str, data: dict | None = None):
        self._emit("settlement", kind="ok", message=text, data=data)

    def override(self, text: str, data: dict | None = None):
        self._emit("override", kind="sys", message=text, data=data)
