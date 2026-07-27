import { Bot, ChevronDown, Landmark, ShieldAlert, ShieldCheck } from 'lucide-react'
import { APP, COMPANY } from '../data'
import { cx, inr } from '../format'
import { Card, Pill, ScoreGauge, SectionLabel, TraceConsole } from './ui'

const OUTCOME_META = {
  approved: { pill: <Pill tone="emerald">Agent: APPROVE</Pill>, note: 'Auto-disbursed under your delegated mandate.' },
  conditional: { pill: <Pill tone="amber">Agent: CONDITIONAL</Pill>, note: 'Within delegated limits at the reduced advance — manual review available on request.' },
  declined: { pill: <Pill tone="red">Agent: DECLINE</Pill>, note: 'Blocked by the fraud engine before reaching your book.' },
}

function FactGrid({ deal }) {
  const d = deal.decision
  const facts = [
    ['Exporter', COMPANY.short],
    ['GST turnover', '₹4.2 Cr · 24/24 filings on time'],
    ['Bank inflows', '₹38.6L avg monthly · 0 bounces'],
    ['Buyer', deal.invoice.buyer.name],
    ['Invoice', `${inr(deal.invoice.amount)} · due ${deal.invoice.due}`],
    ['Lien registry', d.outcome === 'declined' ? `MATCH — ${d.evidence.lender} (${d.evidence.financedOn})` : 'Clean — no prior pledge'],
  ]
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5">
      {facts.map(([k, v]) => (
        <div key={k}>
          <div className="text-[11px] text-slate-400 font-medium">{k}</div>
          <div className={cx('text-[13px] font-semibold', v.startsWith('MATCH') ? 'text-red-600' : 'text-slate-800')}>{v}</div>
        </div>
      ))}
    </div>
  )
}

function DealCard({ deal }) {
  const d = deal.decision
  const meta = OUTCOME_META[d.outcome]
  const declined = d.outcome === 'declined'

  return (
    <Card className={cx('overflow-hidden', declined && 'border-red-300')}>
      <div className={cx('px-5 py-4 border-b flex flex-wrap items-center gap-3', declined ? 'bg-red-50 border-red-100' : 'bg-slate-50 border-slate-100')}>
        {declined
          ? <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          : <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0" />}
        <div className="flex-1 min-w-0">
          <div className="font-bold text-slate-900 text-sm">{deal.invoice.code} · {COMPANY.short} → {deal.invoice.buyer.name}</div>
          <div className="text-xs text-slate-500">{deal.invoice.goods}</div>
        </div>
        <div className="font-extrabold text-slate-900 tabular-nums">{inr(deal.invoice.amount)}</div>
        {meta.pill}
      </div>

      <div className="p-5 flex flex-col md:flex-row gap-6">
        <div className="flex-1 space-y-4">
          <FactGrid deal={deal} />
          <div className={cx('rounded-xl border px-4 py-3 text-[13px] leading-relaxed', declined ? 'bg-red-50 border-red-200 text-red-700' : 'bg-blue-50 border-blue-100 text-slate-600')}>
            <span className="inline-flex items-center gap-1.5 font-bold text-slate-800 mr-1">
              <Bot className="h-3.5 w-3.5 text-blue-600" /> Agent:
            </span>
            {d.reasons[0]} <span className="text-slate-400">·</span> {meta.note}
          </div>
        </div>
        <div className="flex md:flex-col items-center justify-center gap-2 shrink-0">
          {declined ? (
            <div className="text-center px-6">
              <div className="text-3xl font-extrabold text-red-600">✕</div>
              <div className="text-xs font-bold text-red-600 mt-1">FRAUD BLOCK</div>
              <div className="text-[11px] text-slate-400 mt-0.5">{d.evidence.ref}</div>
            </div>
          ) : (
            <ScoreGauge score={d.score} band={d.band} size={130} />
          )}
        </div>
      </div>

      <details className="group border-t border-slate-100">
        <summary className="flex items-center gap-2 cursor-pointer select-none px-5 py-3 text-xs font-semibold text-slate-500 hover:bg-slate-50">
          <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" />
          Reasoning trace ({deal.trace.length} events)
        </summary>
        <div className="px-5 pb-5">
          <TraceConsole lines={deal.trace} live={false} heightClass="h-64" />
        </div>
      </details>
    </Card>
  )
}

export default function Financier({ deals }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
          <Landmark className="h-6 w-6 text-blue-700" /> {APP.financier} — deal desk
        </h1>
        <p className="mt-1.5 text-sm text-slate-500">
          The same deals, as your lending partner sees them: score, evidence and the full agent reasoning — decision-ready.
        </p>
      </div>

      <Card className="p-4 flex flex-wrap items-center gap-x-6 gap-y-2 bg-gradient-to-r from-[#0b1d3a] to-[#13294f] border-blue-900 text-white">
        <span className="text-xs font-bold tracking-widest text-blue-300">DELEGATED MANDATE</span>
        <span className="text-sm">Auto-disburse when: score ≥ 70 · exposure ≤ ₹25L · tenor ≤ 90 days</span>
        <Pill tone="navy" className="ml-auto">Powered by {APP.name}</Pill>
      </Card>

      {deals.length === 0 ? (
        <Card className="p-10 text-center">
          <Bot className="h-10 w-10 text-slate-300 mx-auto" />
          <div className="mt-3 font-semibold text-slate-700">No underwritten deals yet</div>
          <p className="mt-1 text-sm text-slate-500">
            Switch to the <span className="font-semibold">Exporter</span> view and run a financing request — it will appear here instantly.
          </p>
        </Card>
      ) : (
        <div className="space-y-5">
          <SectionLabel>Underwritten this session</SectionLabel>
          {deals.map((deal) => <DealCard key={deal.invoice.id} deal={deal} />)}
        </div>
      )}
    </div>
  )
}
