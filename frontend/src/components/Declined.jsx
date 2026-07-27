import { ArrowRight, Ban, ChevronDown, ShieldAlert } from 'lucide-react'
import { inr } from '../format'
import { Button, Card, TraceConsole, useToast } from './ui'

export default function Declined({ run, onHome }) {
  const { invoice, decision, trace } = run
  const ev = decision.evidence
  const { show, node: toastNode } = useToast()

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* red hero */}
      <div className="rounded-2xl bg-gradient-to-br from-red-600 to-red-700 text-white p-6 sm:p-8 shadow-xl shadow-red-600/25 animate-rise">
        <div className="flex items-start gap-4">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 shrink-0 animate-ring-red">
            <ShieldAlert className="h-8 w-8 animate-pop" />
          </span>
          <div>
            <div className="text-[11px] font-bold tracking-widest text-red-100">
              FINANCING DECLINED{ev ? ' · FRAUD RISK' : ''}
            </div>
            <h1 className="mt-1 text-xl sm:text-2xl font-extrabold leading-snug">{decision.headline}</h1>
            <p className="mt-2 text-sm text-red-50/90 leading-relaxed">
              {ev ? (
                <>The agent found an <span className="font-bold">active lien</span> on this exact invoice
                ({invoice.irn}) in the central receivables registry. The same {inr(invoice.amount)} receivable
                cannot back two loans.</>
              ) : decision.banner}
            </p>
          </div>
        </div>

        {/* registry evidence — the actual row the fraud node found */}
        {ev && (
          <div className="mt-5 rounded-xl bg-[#12060a]/45 border border-red-400/40 p-4">
            <div className="text-[11px] font-bold tracking-widest text-red-200 mb-3">
              REGISTRY RECORD — READ LIVE FROM financing_registry
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
              {[
                ['Financed by', ev.lender],
                ['Financed on', ev.financedOn],
                ['Registry reference', ev.ref],
                ['Lien status', ev.status],
              ].map(([k, v]) => (
                <div key={k} className="flex flex-col">
                  <span className="text-[11px] text-red-200/80">{k}</span>
                  <span className="font-semibold font-mono text-[13px]">{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <Card className="p-5">
        <div className="font-bold text-slate-900 text-sm mb-3">Why the agent declined</div>
        <ul className="space-y-2.5">
          {decision.reasons.map((r, i) => (
            <li key={i} className="flex items-start gap-2.5 text-[13px] leading-relaxed text-slate-600">
              <Ban className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" /> {r}
            </li>
          ))}
        </ul>
      </Card>

      {decision.nextSteps && (
        <Card className="p-5 bg-slate-50">
          <div className="font-bold text-slate-900 text-sm mb-3">What happens next</div>
          <ul className="space-y-2.5">
            {decision.nextSteps.map((r, i) => (
              <li key={i} className="flex items-start gap-2.5 text-[13px] leading-relaxed text-slate-600">
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 mt-0.5 shrink-0" /> {r}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <details className="group">
        <summary className="flex items-center gap-2 cursor-pointer select-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
          <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
          Full audit trace ({trace?.length ?? 0} events)
        </summary>
        <div className="mt-3">
          <TraceConsole lines={trace ?? []} live={false} heightClass="h-80" />
        </div>
      </details>

      <div className="flex flex-col sm:flex-row gap-3">
        {ev && (
          <Button variant="ghost" size="lg" className="flex-1"
                  onClick={() => show(`Dispute logged against ${ev.ref} — the registry operator responds within 2 business days (simulated).`)}>
            Raise a dispute
          </Button>
        )}
        <Button variant="dark" size="lg" className="flex-1" onClick={onHome}>
          Back to dashboard
        </Button>
      </div>
      {toastNode}
    </div>
  )
}
