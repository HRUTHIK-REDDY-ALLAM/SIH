import { ArrowLeft, ArrowRight, Banknote, CheckCircle2, ChevronDown, Landmark, Scale, Sparkles } from 'lucide-react'
import { APP } from '../data'
import { cx, inr } from '../format'
import { Button, Card, Pill, ScoreGauge, SectionLabel, TraceConsole, useToast } from './ui'

function Row({ label, value, strong, negative }) {
  return (
    <div className={cx('flex items-baseline justify-between gap-4 py-2.5', strong && 'py-3')}>
      <span className={cx('text-sm', strong ? 'font-bold text-slate-900' : 'text-slate-500')}>{label}</span>
      <span className={cx(
        'tabular-nums tracking-tight',
        strong ? 'text-xl font-extrabold text-slate-900' : negative ? 'text-sm font-semibold text-red-600' : 'text-sm font-semibold text-slate-800',
      )}>
        {value}
      </span>
    </div>
  )
}

export default function Offer({ run, onAccept, onBack }) {
  const { invoice, decision, trace } = run
  const conditional = decision.outcome === 'conditional'
  const { show, node: toastNode } = useToast()

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer">
        <ArrowLeft className="h-4 w-4" /> Back to the underwriting run
      </button>

      {/* status banner */}
      <div className={cx(
        'rounded-2xl border p-4 flex items-center gap-3 animate-rise',
        conditional ? 'bg-amber-50 border-amber-300' : 'bg-emerald-50 border-emerald-300',
      )}>
        {conditional
          ? <Scale className="h-6 w-6 text-amber-600 shrink-0 animate-pop" />
          : <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0 animate-pop" />}
        <div>
          <div className={cx('font-bold', conditional ? 'text-amber-800' : 'text-emerald-800')}>{decision.headline}</div>
          <div className={cx('text-sm', conditional ? 'text-amber-700' : 'text-emerald-700')}>{decision.banner}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
        {/* offer card */}
        <Card className="lg:col-span-3 overflow-hidden">
          <div className="px-6 pt-5 pb-4 border-b border-slate-100 flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Financing offer</div>
              <div className="mt-0.5 font-bold text-slate-900">{invoice.code} · {invoice.buyer.name}</div>
            </div>
            <Pill tone={conditional ? 'amber' : 'emerald'}>{decision.advancePct}% advance</Pill>
          </div>

          <div className="px-6 py-3 divide-y divide-slate-100">
            <Row label="Invoice value" value={inr(invoice.amount)} />
            <Row label={`Advance (${decision.advancePct}% of invoice)`} value={inr(decision.advance)} />
            <Row label={`Flat fee (${decision.feePct} of advance)`} value={`− ${inr(decision.fee)}`} negative />
            <Row label="You receive today" value={inr(decision.net)} strong />
            <Row label={`Balance released when the buyer pays (${invoice.due})`} value={inr(decision.balance)} />
          </div>

          <div className="mx-6 mb-5 rounded-xl bg-slate-50 border border-slate-200 px-4 py-3 flex items-start gap-2.5">
            <Landmark className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Disbursed by <span className="font-semibold text-slate-700">{APP.financier}</span> (RBI-registered).
              TradeBridge AI underwrites the deal — licensed partners lend. The loan settles itself when {invoice.buyer.name.replace(' Pte. Ltd.', '')} pays.
            </p>
          </div>

          <div className="px-6 pb-6 flex flex-col sm:flex-row gap-3">
            <Button size="lg" variant={conditional ? 'primary' : 'success'} className="flex-1" onClick={onAccept}>
              <Banknote className="h-4.5 w-4.5" /> Accept — get {inr(decision.net)} now
            </Button>
            {conditional && (
              <Button
                size="lg" variant="ghost" className="flex-1"
                onClick={() => show('Routed to Nexa Capital credit desk — a human underwriter responds within 1 business day (simulated).')}
              >
                Request manual review for a higher advance
              </Button>
            )}
          </div>
        </Card>

        {/* why + score */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-5">
            <div className="flex items-center justify-between gap-3">
              <SectionLabel>Agent risk assessment</SectionLabel>
            </div>
            <div className="flex justify-center -mt-1"><ScoreGauge score={decision.score} band={decision.band} /></div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <span className="font-bold text-slate-900 text-sm">Why the agent decided this</span>
            </div>
            <ul className="space-y-2.5">
              {decision.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2.5 text-[13px] leading-relaxed text-slate-600">
                  <ArrowRight className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" /> {r}
                </li>
              ))}
            </ul>
          </Card>

          <details className="group">
            <summary className="flex items-center gap-2 cursor-pointer select-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
              Full reasoning trace ({trace.length} events)
            </summary>
            <div className="mt-3">
              <TraceConsole lines={trace} live={false} heightClass="h-80" />
            </div>
          </details>
        </div>
      </div>
      {toastNode}
    </div>
  )
}
