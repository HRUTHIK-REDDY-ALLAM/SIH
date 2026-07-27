import { useState } from 'react'
import { ArrowLeft, CheckCircle2, FileText, Landmark, Lock, Sparkles } from 'lucide-react'
import { CONSENTS } from '../data'
import { cx, inr } from '../format'
import { Button, Card, Pill } from './ui'

const CONSENT_ICONS = { gst: FileText, aa: Landmark }

export default function Consent({ invoice, onBack, onDone }) {
  const [approved, setApproved] = useState({})
  const allApproved = CONSENTS.every((c) => approved[c.id])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer">
        <ArrowLeft className="h-4 w-4" /> Change invoice
      </button>

      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Approve data sharing</h1>
        <p className="mt-1.5 text-sm text-slate-500">
          To underwrite <span className="font-semibold text-slate-700">{invoice.code}</span> ({inr(invoice.amount)} · {invoice.buyer.name}),
          the agent needs two one-tap consents. Read-only, purpose-bound, revocable.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CONSENTS.map((c) => {
          const Icon = CONSENT_ICONS[c.id]
          const ok = approved[c.id]
          return (
            <Card key={c.id} className={cx('p-5 flex flex-col transition-all', ok && 'border-emerald-300 ring-2 ring-emerald-500/15')}>
              <div className="flex items-center gap-3">
                <span className={cx(
                  'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
                  ok ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600',
                )}>
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <div className="font-semibold text-slate-900 text-sm">{c.title}</div>
                  <div className="text-xs text-slate-500">{c.provider}</div>
                </div>
              </div>

              <ul className="mt-4 space-y-2 flex-1">
                {c.points.map((p) => (
                  <li key={p} className="flex items-start gap-2 text-xs text-slate-600">
                    <Lock className="h-3.5 w-3.5 text-slate-400 mt-px shrink-0" /> {p}
                  </li>
                ))}
              </ul>

              {ok ? (
                <div className="mt-4 flex items-center gap-2 rounded-xl bg-emerald-50 border border-emerald-200 px-3.5 py-2.5 animate-pop">
                  <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600" />
                  <div className="text-xs">
                    <span className="font-semibold text-emerald-700">Approved</span>
                    <span className="text-emerald-600/80"> · consent ID {c.consentId}</span>
                  </div>
                </div>
              ) : (
                <Button className="mt-4 w-full" onClick={() => setApproved((a) => ({ ...a, [c.id]: true }))}>
                  Approve
                </Button>
              )}
            </Card>
          )
        })}
      </div>

      <Card className="p-5 flex flex-col sm:flex-row items-center gap-4">
        <div className="flex-1 text-center sm:text-left">
          <div className="font-semibold text-slate-900 text-sm">
            {allApproved ? 'Both consents in place — the agent is ready.' : 'Approve both consents to continue'}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            Simulated consent — this prototype never touches real credentials or live data.
          </div>
        </div>
        <Button size="lg" variant="hero" disabled={!allApproved} onClick={onDone} className={cx(allApproved && 'animate-ring')}>
          <Sparkles className="h-4 w-4" /> Start AI underwriting
        </Button>
      </Card>

      {!allApproved && (
        <div className="flex justify-center">
          <Pill tone="slate">{Object.keys(approved).length} of {CONSENTS.length} approved</Pill>
        </div>
      )}
    </div>
  )
}
