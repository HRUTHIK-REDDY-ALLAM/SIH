import { ArrowRight, Banknote, CheckCircle2, Landmark, RefreshCw } from 'lucide-react'
import { APP, COMPANY } from '../data'
import { cx, inr } from '../format'
import { Button, Card, Pill } from './ui'

function TimelineNode({ icon: Icon, title, text, first, last, done }) {
  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {!last && <span className="absolute left-[19px] top-11 bottom-0 w-0.5 bg-slate-200 rounded" />}
      <span className={cx(
        'flex h-10 w-10 items-center justify-center rounded-full border-2 shrink-0 z-10',
        done ? 'bg-emerald-500 border-emerald-500 text-white' : 'bg-white border-slate-300 text-slate-400',
      )}>
        <Icon className="h-4.5 w-4.5" />
      </span>
      <div className={cx('pt-1', !done && 'opacity-80')}>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900 text-sm">{title}</span>
          {first && <Pill tone="emerald">Done</Pill>}
        </div>
        <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">{text}</p>
      </div>
    </div>
  )
}

export default function Disbursed({ run, onHome }) {
  const { invoice, decision } = run
  const st = decision.settlement

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* success hero */}
      <div className="text-center pt-4">
        <div className="relative inline-flex">
          <svg viewBox="0 0 64 64" className="h-24 w-24">
            <circle cx="32" cy="32" r="28" fill="none" stroke="#a7f3d0" strokeWidth="4" />
            <circle cx="32" cy="32" r="28" fill="none" stroke="#059669" strokeWidth="4" strokeLinecap="round" pathLength="100" className="check-draw" transform="rotate(-90 32 32)" />
            <path d="M20 33 L29 42 L45 24" fill="none" stroke="#059669" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" pathLength="100" className="check-draw" />
          </svg>
        </div>
        <h1 className="mt-3 text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
          {inr(decision.net)} is on its way
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          NEFT to {COMPANY.bank} · {st.utr} <span className="text-slate-400">(simulated)</span>
        </p>
        <div className="mt-3 flex justify-center">
          <Pill tone="emerald">Funds disbursed by {APP.financier}</Pill>
        </div>
      </div>

      {/* repayment timeline */}
      <Card className="p-6">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-5">
          Repayment timeline — nothing more for you to do
        </div>
        <TimelineNode
          first done icon={Banknote}
          title={`Today — ${inr(decision.net)} disbursed to you`}
          text={`${decision.advancePct}% advance of ${inr(decision.advance)}, minus the ${decision.feePct} flat fee (${inr(decision.fee)}). No EMIs, no collateral.`}
        />
        <TimelineNode
          icon={Landmark}
          title={`${st.payDate} — ${st.payer} pays the invoice`}
          text={`${inr(invoice.amount)} lands in the TradeBridge escrow account (${st.tenorDays}-day tenor).`}
        />
        <TimelineNode
          icon={RefreshCw}
          title="Same day — the loan settles itself"
          text={`${inr(decision.advance)} advance is auto-recovered by ${APP.financier}. You never have to remember a repayment.`}
        />
        <TimelineNode
          last icon={CheckCircle2}
          title={`Balance released to you — ${inr(decision.balance)}`}
          text={`Total received: ${st.totalToYou} of ${inr(invoice.amount)} · all-in cost ${st.allInCost}.`}
        />
      </Card>

      <div className="flex justify-center">
        <Button variant="dark" size="lg" onClick={onHome}>
          Back to dashboard <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
