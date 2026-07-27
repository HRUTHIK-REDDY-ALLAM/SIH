import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, CheckCircle2, FileText, Landmark, Lock, Sparkles } from 'lucide-react'
import { api } from '../api'
import { CONSENT_CARDS } from '../data'
import { cx, inr } from '../format'
import { Button, Card, ErrorBox, Pill, Spinner } from './ui'

const CONSENT_ICONS = { gst: FileText, aa: Landmark }

export default function Consent({ token, invoice, onBack, onDone }) {
  const [granted, setGranted] = useState(null) // {gst: {...}, aa: {...}}
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api('/api/consents', { token })
      .then((list) => setGranted(Object.fromEntries(list.map((c) => [c.ctype, c]))))
      .catch((e) => setError(e.message))
  }, [token])

  useEffect(() => { load() }, [load])

  const approve = async (ctype) => {
    setBusy(ctype)
    setError(null)
    try {
      const consent = await api('/api/consents', { method: 'POST', body: { ctype }, token })
      setGranted((g) => ({ ...g, [ctype]: consent }))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  const allApproved = granted && CONSENT_CARDS.every((c) => granted[c.id])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer">
        <ArrowLeft className="h-4 w-4" /> Change invoice
      </button>

      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Approve data sharing</h1>
        <p className="mt-1.5 text-sm text-slate-500">
          To underwrite <span className="font-semibold text-slate-700">{invoice.code}</span> ({inr(invoice.amount)} · {invoice.buyer.name}),
          the agent needs two consents. They are stored as records in the consents table and the API refuses to
          start underwriting without them.
        </p>
      </div>

      {error && <ErrorBox title="Consent request failed" detail={error} onRetry={load} />}
      {granted === null && !error && <Spinner label="Checking existing consents…" />}

      {granted !== null && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CONSENT_CARDS.map((c) => {
            const Icon = CONSENT_ICONS[c.id]
            const rec = granted[c.id]
            return (
              <Card key={c.id} className={cx('p-5 flex flex-col transition-all', rec && 'border-emerald-300 ring-2 ring-emerald-500/15')}>
                <div className="flex items-center gap-3">
                  <span className={cx(
                    'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
                    rec ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600',
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

                {rec ? (
                  <div className="mt-4 rounded-xl bg-emerald-50 border border-emerald-200 px-3.5 py-2.5 animate-pop">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600" />
                      <span className="text-xs font-semibold text-emerald-700">Active consent on record</span>
                    </div>
                    <div className="mt-1 text-[11px] text-emerald-600/80">
                      ID {rec.consent_ref} · granted {rec.granted_on} · expires {rec.expires_on}
                    </div>
                  </div>
                ) : (
                  <Button className="mt-4 w-full" disabled={busy === c.id} onClick={() => approve(c.id)}>
                    {busy === c.id ? 'Recording consent…' : 'Approve'}
                  </Button>
                )}
              </Card>
            )
          })}
        </div>
      )}

      <Card className="p-5 flex flex-col sm:flex-row items-center gap-4">
        <div className="flex-1 text-center sm:text-left">
          <div className="font-semibold text-slate-900 text-sm">
            {allApproved ? 'Both consents on record — the agent is cleared to pull data.' : 'Approve both consents to continue'}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            Consents persist across sessions and are re-checked inside the pipeline's Data Gathering node.
          </div>
        </div>
        <Button size="lg" variant="hero" disabled={!allApproved} onClick={onDone} className={cx(allApproved && 'animate-ring')}>
          <Sparkles className="h-4 w-4" /> Start AI underwriting
        </Button>
      </Card>

      {granted !== null && !allApproved && (
        <div className="flex justify-center">
          <Pill tone="slate">{Object.keys(granted).length} of {CONSENT_CARDS.length} approved</Pill>
        </div>
      )}
    </div>
  )
}
